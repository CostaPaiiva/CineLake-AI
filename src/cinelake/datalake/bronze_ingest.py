"""Pipeline para popular a camada bronze do Data Lake com dados brutos do MovieLens e do TMDB."""

import json
import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import text

from cinelake.config import settings
from cinelake.db import get_engine
from cinelake.datalake.minio_client import criar_cliente_minio, garantir_bucket, fazer_upload_parquet
from cinelake.ingestion.movielens.ingest import _contar_registros  # Reutilizamos função de contagem de registros

# Inicializa o sistema de logs para rastreamento de progresso e erros
logger = logging.getLogger(__name__)


def _converter_csv_para_parquet(caminho_csv: Path, arquivo_parquet: Path) -> None:
    """Lê um arquivo local CSV e o converte para o formato colunar Parquet.
    
    A conversão reduz consideravelmente o tamanho do arquivo e otimiza a leitura posterior.
    """
    logger.info("Convertendo %s para %s", caminho_csv, arquivo_parquet)
    # Lê os dados do arquivo CSV
    df = pd.read_csv(caminho_csv)
    # Converte e salva localmente como Parquet usando o engine 'pyarrow'
    df.to_parquet(arquivo_parquet, index=False, engine="pyarrow")
    logger.debug("Arquivo Parquet criado: %s", arquivo_parquet)


def _converter_jsons_para_parquet(diretorio: Path, arquivo_parquet: Path) -> None:
    """Agrupa múltiplos arquivos JSON de um diretório e os compila em um único arquivo Parquet."""
    registros = []
    # Itera por todos os arquivos JSON do diretório informado
    for arquivo_json in diretorio.glob("*.json"):
        with arquivo_json.open("r", encoding="utf-8") as f:
            registros.append(json.load(f))
    # Cria o DataFrame Pandas unindo todos os registros JSON
    df = pd.DataFrame(registros)
    # Salva o resultado no formato Parquet
    df.to_parquet(arquivo_parquet, index=False, engine="pyarrow")


def _registrar_batch(conn, fonte: str, status: str, rows_processed: int, error_message: str | None = None) -> int:
    """Insere o log de execução do lote (batch) de ingestão na tabela 'ingestion_batch' do PostgreSQL.
    
    Permite auditar quando a ingestão rodou, quantos dados processou e se houve falhas.
    """
    from datetime import datetime, timezone

    agora = datetime.now(timezone.utc)
    # Executa o comando de inserção e retorna a chave primária auto-incrementada (batch_id)
    resultado = conn.execute(
        text(
            "INSERT INTO ingestion_batch (source, status, started_at, rows_processed, rows_inserted, error_message) "
            "VALUES (:source, :status, :started_at, :rows_processed, :rows_inserted, :error_message) RETURNING batch_id"
        ),
        {
            "source": fonte,
            "status": status,
            "started_at": agora,
            "rows_processed": rows_processed,
            "rows_inserted": rows_processed,  # Simplificação (assume que todas as linhas processadas foram inseridas)
            "error_message": error_message,
        },
    )
    batch_id = resultado.scalar()
    return int(batch_id)


def ingerir_bronze(diretorio_movielens: Path, diretorio_tmdb: Path) -> dict:
    """Orquestra a ingestão da camada Bronze.
    
    1. Converte dados brutos locais (CSV do MovieLens e JSON do TMDB) para Parquet.
    2. Garante a existência do bucket no MinIO.
    3. Faz o upload dos arquivos Parquet resultantes para o MinIO.
    4. Registra a execução no banco de dados para fins de monitoramento.

    Args:
        diretorio_movielens: Caminho local contendo os arquivos CSV (movies, ratings, etc.).
        diretorio_tmdb: Caminho local contendo os JSONs das APIs (details, credits, etc.).

    Returns:
        Dicionário resumindo a quantidade de arquivos enviados e possíveis erros.
    """
    # Obtém o motor de conexão com o banco de dados
    engine = get_engine()
    # Conecta com a API do MinIO
    cliente = criar_cliente_minio()
    # Garante que o bucket do Data Lake (ex: data-lake) esteja criado no MinIO
    garantir_bucket(cliente, settings.minio_bucket)

    # Cria diretório temporário local para salvar os arquivos Parquet antes do upload
    arquivos_temporarios = Path("data/tmp")
    arquivos_temporarios.mkdir(parents=True, exist_ok=True)

    total_arquivos = 0
    erro = None

    try:
        # Abre transação no PostgreSQL
        with engine.begin() as conn:
            # === Processamento do MovieLens (salvos em: bronze/movielens) ===
            for nome in ["movies", "ratings", "tags", "links"]:
                csv_path = diretorio_movielens / f"{nome}.csv"
                if not csv_path.exists():
                    logger.warning("CSV não encontrado: %s", csv_path)
                    continue

                parquet_tmp = arquivos_temporarios / f"{nome}.parquet"
                # Converte o CSV bruto local em Parquet
                _converter_csv_para_parquet(csv_path, parquet_tmp)

                # Envia o Parquet convertido para a pasta da camada bronze no MinIO
                chave = f"bronze/movielens/{nome}.parquet"
                fazer_upload_parquet(cliente, settings.minio_bucket, chave, parquet_tmp)
                total_arquivos += 1

            # === Processamento do TMDB (salvos em: bronze/tmdb) ===
            for tipo in ["details", "credits", "keywords"]:
                diretorio_tipo = diretorio_tmdb  # Os JSONs encontram-se na raiz
                arquivos_jsons = list(diretorio_tipo.glob(f"*_{tipo}.json"))
                if not arquivos_jsons:
                    logger.warning("Nenhum JSON do tipo %s encontrado", tipo)
                    continue

                # Agrupa e lê todos os arquivos JSON de um mesmo tipo
                registros = []
                for json_path in arquivos_jsons:
                    with json_path.open("r", encoding="utf-8") as f:
                        registros.append(json.load(f))

                # Estrutura em um DataFrame do Pandas
                df = pd.DataFrame(registros)
                parquet_tmp = arquivos_temporarios / f"tmdb_{tipo}.parquet"
                # Converte o bloco de registros JSON compilado em um único arquivo Parquet
                df.to_parquet(parquet_tmp, index=False, engine="pyarrow")

                # Envia o arquivo unificado para o MinIO
                chave = f"bronze/tmdb/{tipo}.parquet"
                fazer_upload_parquet(cliente, settings.minio_bucket, chave, parquet_tmp)
                total_arquivos += 1

            # Registra no PostgreSQL o sucesso do lote de ingestão bronze
            _registrar_batch(conn, "datalake_bronze", "success", total_arquivos)
            logger.info("Ingestão bronze concluída com sucesso. Arquivos enviados: %d", total_arquivos)

    except Exception as exc:
        erro = str(exc)
        logger.exception("Erro na ingestão bronze")
        # Registra a falha no banco de dados
        with engine.begin() as conn:
            _registrar_batch(conn, "datalake_bronze", "failed", total_arquivos, error_message=erro)
        raise

    return {"arquivos_enviados": total_arquivos, "erro": erro}