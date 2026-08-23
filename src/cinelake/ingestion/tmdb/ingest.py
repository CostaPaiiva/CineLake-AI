"""Pipeline de ingestão incremental do TMDb para metadados de filmes."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from cinelake.config import settings
from cinelake.db import get_engine
from cinelake.ingestion.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


def _obter_watermark(conn: Connection) -> int:
    """Retorna o último movie_id processado com sucesso a partir da tabela de estado."""
    resultado = conn.execute(
        text("SELECT last_processed_movie_id FROM tmdb_ingestion_state WHERE id = 1")
    )
    val = resultado.scalar()
    watermark = int(val) if val is not None else 0
    logger.info("Watermark atual: %s", watermark)
    return watermark


def _atualizar_watermark(conn: Connection, movie_id: int) -> None:
    """Atualiza o cursor (watermark) para registrar o progresso do filme recém-processado."""
    agora = datetime.now(timezone.utc)
    conn.execute(
        text(
            """
            UPDATE tmdb_ingestion_state
            SET last_processed_movie_id = :movie_id,
                last_run_at = :agora,
                updated_at = :agora
            WHERE id = 1
            """
        ),
        {"movie_id": movie_id, "agora": agora},
    )


def _criar_batch(conn: Connection, fonte: str) -> int:
    """Cria um novo registro na tabela de auditoria (ingestion_batch) e retorna o batch_id."""
    agora = datetime.now(timezone.utc)
    resultado = conn.execute(
        text(
            """
            INSERT INTO ingestion_batch (source, status, started_at)
            VALUES (:source, 'running', :started_at)
            RETURNING batch_id
            """
        ),
        {"source": fonte, "started_at": agora},
    )
    val = resultado.scalar()
    batch_id = int(val) if val is not None else 0
    logger.info("Batch criado: %s", batch_id)
    return batch_id


def _finalizar_batch(
    conn: Connection,
    batch_id: int,
    status: str,
    rows_processed: int,
    rows_success: int,
    error_message: str | None = None,
) -> None:
    """Atualiza o registro do lote na tabela ingestion_batch com o status final e métricas."""
    agora = datetime.now(timezone.utc)
    conn.execute(
        text(
            """
            UPDATE ingestion_batch
            SET status = :status,
                finished_at = :finished_at,
                rows_processed = :rows_processed,
                rows_inserted = :rows_inserted,
                error_message = :error_message
            WHERE batch_id = :batch_id
            """
        ),
        {
            "status": status,
            "finished_at": agora,
            "rows_processed": rows_processed,
            "rows_inserted": rows_success,
            "error_message": error_message,
            "batch_id": batch_id,
        },
    )


def _salvar_json(
    diretorio: Path,
    movie_id: int,
    tipo: str,
    dados: dict[str, Any],
) -> None:
    """Salva os dados brutos recebidos da API do TMDb em um arquivo JSON estruturado no disco."""
    # Se a resposta estiver vazia (ex: 404), não cria arquivo vazio
    if not dados:
        logger.debug("Sem dados para movie_id=%s tipo=%s", movie_id, tipo)
        return

    arquivo = diretorio / f"{movie_id}_{tipo}.json"
    with arquivo.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    logger.debug("JSON salvo: %s", arquivo)


def ingerir_tmdb(
    diretorio_saida: Path,
    requests_per_second: float = 4.0,
    max_filmes_por_execucao: int | None = None,
) -> dict[str, int]:
    """Executa a ingestão incremental de metadados do TMDb para os filmes cadastrados.

    Lê os filmes a partir do último watermark salvo, consulta a API e persiste os JSONs.

    Args:
        diretorio_saida: Diretório onde os arquivos JSON brutos serão salvos.
        requests_per_second: Limite de requisições por segundo para o rate limit.
        max_filmes_por_execucao: Limite opcional para processamento em lotes menores.

    Returns:
        Dicionário com resumo da execução (batch_id, processados e sucesso).
    """
    engine: Engine = get_engine()
    # Inicializa o cliente HTTP com a chave configurada no ambiente
    cliente = TMDBClient(
        api_key=settings.tmdb_api_key,
        requests_per_second=requests_per_second,
        timeout=10,
    )

    # Garante que o diretório de destino dos arquivos JSON exista
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    total_processado = 0
    total_sucesso = 0
    batch_id: int | None = None

    try:
        with engine.begin() as conn:
            # 1. Cria o lote de auditoria
            batch_id = _criar_batch(conn, "tmdb")

            # 2. Obtém o ponto de parada anterior (watermark)
            watermark = _obter_watermark(conn)

            # 3. Busca próximos movie_ids e seus respectivos tmdb_ids a partir da tabela links
            query = """
                SELECT movie_id, tmdb_id
                FROM links
                WHERE movie_id > :watermark AND tmdb_id IS NOT NULL
                ORDER BY movie_id
            """
            if max_filmes_por_execucao:
                query += " LIMIT :limite"
                params = {
                    "watermark": watermark,
                    "limite": max_filmes_por_execucao,
                }
            else:
                params = {"watermark": watermark}

            resultado = conn.execute(text(query), params)
            # Armazena tuplas (movie_id, tmdb_id)
            filmes = [(int(row[0]), int(row[1])) for row in resultado]

            logger.info("Filmes a processar nesta execução: %d", len(filmes))

            # 4. Itera sobre cada filme buscando os metadados na API do TMDb usando o tmdb_id
            for movie_id, tmdb_id in filmes:
                total_processado += 1
                logger.info("Processando movie_id=%s (tmdb_id=%s)", movie_id, tmdb_id)

                try:
                    # Faz as 3 requisições necessárias usando o ID correto do TMDb
                    detalhes = cliente.get_movie_details(tmdb_id)
                    creditos = cliente.get_movie_credits(tmdb_id)
                    keywords = cliente.get_movie_keywords(tmdb_id)

                    # Persiste os dados brutos no Data Lake usando o movie_id para manter o padrão
                    _salvar_json(diretorio_saida, movie_id, "details", detalhes)
                    _salvar_json(diretorio_saida, movie_id, "credits", creditos)
                    _salvar_json(diretorio_saida, movie_id, "keywords", keywords)

                    total_sucesso += 1
                    # Atualiza o watermark imediatamente para persistir o checkpoint
                    _atualizar_watermark(conn, movie_id)
                    logger.info("Sucesso para movie_id=%s", movie_id)

                except Exception:
                    logger.exception("Erro ao processar movie_id=%s", movie_id)
                    # Interrompe a execução para não pular filmes silenciosamente
                    raise

            # 5. Finaliza o lote com status de sucesso
            _finalizar_batch(
                conn,
                batch_id,
                "success",
                rows_processed=total_processado,
                rows_success=total_sucesso,
            )
            logger.info("Ingestão TMDB concluída. Batch %s", batch_id)

    except Exception as exc:
        # Se ocorrer qualquer falha crítica, registra o erro no batch usando conexão limpa
        logger.exception("Erro durante a ingestão TMDB")
        if batch_id is not None:
            with engine.begin() as conn_err:
                _finalizar_batch(
                    conn_err,
                    batch_id,
                    "failed",
                    rows_processed=total_processado,
                    rows_success=total_sucesso,
                    error_message=str(exc),
                )
        raise

    return {
        "batch_id": batch_id or 0,
        "rows_processed": total_processado,
        "rows_success": total_sucesso,
    }
