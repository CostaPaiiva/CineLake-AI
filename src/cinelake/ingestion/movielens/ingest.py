"""Pipeline de ingestão idempotente do MovieLens para PostgreSQL."""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Importa os módulos necessários do SQLAlchemy Core
from sqlalchemy import column, table, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, Engine

# Importa as configurações do projeto e a conexão com o banco
from cinelake.db import get_engine

# Configuração do logger local para registrar o andamento do processo
logger = logging.getLogger(__name__)

# Definições das tabelas para referência programática no SQLAlchemy Core (sem usar classes ORM)
TABELA_MOVIES = table(
    "movies",
    column("movie_id"),  # Coluna ID do filme
    column("title"),     # Coluna Título
    column("genres"),    # Coluna Gêneros
)

TABELA_RATINGS = table(
    "ratings",
    column("user_id"),   # Coluna ID do usuário
    column("movie_id"),  # Coluna ID do filme
    column("rating"),    # Coluna Nota da avaliação
    column("ts"),        # Coluna Timestamp da avaliação
)

TABELA_TAGS = table(
    "tags",
    column("user_id"),   # Coluna ID do usuário
    column("movie_id"),  # Coluna ID do filme
    column("tag"),       # Coluna Texto da tag
    column("ts"),        # Coluna Timestamp da tag
)

TABELA_LINKS = table(
    "links",
    column("movie_id"),  # Coluna ID do filme no MovieLens
    column("imdb_id"),   # Coluna ID correspondente no IMDb
    column("tmdb_id"),   # Coluna ID correspondente no TMDb
)


def _ler_csv(caminho: Path) -> list[dict[str, str]]:
    """Lê um arquivo CSV e retorna uma lista de dicionários (uma chave por coluna)."""
    # Abre o arquivo com codificação UTF-8
    with caminho.open("r", encoding="utf-8") as arquivo:
        # Usa o DictReader para que cada linha seja um dicionário mapeando cabeçalho -> valor
        leitor = csv.DictReader(arquivo)
        # Converte o gerador em uma lista carregada em memória e a retorna
        return list(leitor)


def _contar_registros(conn: Connection, nome_tabela: str) -> int:
    """Retorna a quantidade total de linhas atualmente em uma tabela (usado para calcular inserções)."""
    # Executa uma consulta direta SELECT COUNT(*) na tabela fornecida
    resultado = conn.execute(text(f"SELECT COUNT(*) FROM {nome_tabela}"))
    # Extrai o primeiro valor numérico retornado do resultado de forma segura para tipos
    val = resultado.scalar()
    return int(val) if val is not None else 0


def _criar_batch(conn: Connection, fonte: str) -> int:
    """Registra o início de uma nova execução de ingestão e retorna seu ID autogerado (batch_id)."""
    # Obtém o timestamp atual no fuso horário UTC
    agora = datetime.now(timezone.utc)
    # Insere uma nova linha na tabela de logs de auditoria marcando o status como em execução ('running')
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
    # Extrai e converte para inteiro o ID gerado pelo RETURNING do PostgreSQL
    val = resultado.scalar()
    batch_id = int(val) if val is not None else 0
    # Exibe no console/log que o lote foi criado com sucesso
    logger.info("Batch criado: %s", batch_id)
    return batch_id


def _finalizar_batch(
    conn: Connection,
    batch_id: int,
    status: str,
    rows_processed: int,
    rows_inserted: int,
    rows_updated: int = 0,
    error_message: str | None = None,
) -> None:
    """Atualiza o registro de controle do lote (batch) com estatísticas finais e status de conclusão/falha."""
    # Obtém o timestamp atual em UTC para marcar a conclusão da tarefa
    agora = datetime.now(timezone.utc)
    # Atualiza as colunas de estatísticas e a mensagem de erro do lote específico
    conn.execute(
        text(
            """
            UPDATE ingestion_batch
            SET status = :status,
                finished_at = :finished_at,
                rows_processed = :rows_processed,
                rows_inserted = :rows_inserted,
                rows_updated = :rows_updated,
                error_message = :error_message
            WHERE batch_id = :batch_id
            """
        ),
        {
            "status": status,
            "finished_at": agora,
            "rows_processed": rows_processed,
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "error_message": error_message,
            "batch_id": batch_id,
        },
    )


def _ingest_arquivo(
    conn: Connection,
    caminho_csv: Path,
    tabela_nome: str,
    colunas: list[str],
    tipo_conflito: str,
    chave_conflito: list[str] | None = None,
    colunas_update: list[str] | None = None,
) -> tuple[int, int]:
    """Processa um arquivo CSV e insere/atualiza os registros no banco de dados.

    Suporta estratégias de resolução de conflito de chave primária:
    - 'nada': Ignora conflitos (Do Nothing)
    - 'atualizar': Sobrescreve dados antigos com os novos (Upsert / Do Update)

    Retorna uma tupla contendo (linhas_processadas, linhas_inseridas).
    """
    # Lê as linhas estruturadas do arquivo CSV
    registros = _ler_csv(caminho_csv)
    # Conta a quantidade total de registros no CSV
    total_processado = len(registros)

    # Se o arquivo estiver vazio, retorna imediatamente 0 processados e 0 inseridos
    if total_processado == 0:
        return 0, 0

    # Obtém o contador de registros atual antes de fazermos qualquer modificação no banco
    contador_antes = _contar_registros(conn, tabela_nome)

    # Lista que guardará os registros devidamente tipados para inserção
    linhas = []
    # Itera sobre cada linha lida do CSV
    for reg in registros:
        linha: dict[str, Any] = {}
        # Itera sobre as colunas que esperamos receber desse arquivo
        for coluna in colunas:
            valor = reg.get(coluna)
            # Se a coluna não existir na linha atual, pula para a próxima
            if valor is None:
                continue
            # Verifica se a coluna deve ser interpretada como inteiro
            if coluna in ("movie_id", "user_id", "ts", "imdb_id", "tmdb_id"):
                # Faz a conversão segura removendo possíveis casas decimais (ex: '1.0' -> 1.0 -> 1)
                linha[coluna] = int(float(valor)) if valor else None
            # Verifica se a coluna deve ser interpretada como decimal (rating do filme)
            elif coluna == "rating":
                linha[coluna] = float(valor)
            # Para colunas de texto (como tag, title, genres), mantém como string original
            else:
                linha[coluna] = valor
        # Adiciona o registro tipado à lista final
        linhas.append(linha)

    # Constrói o comando inicial de INSERT usando o SQLAlchemy Core
    stmt = insert(table(tabela_nome, *[text(c) for c in colunas]))  # type: ignore[arg-type]

    # Configura a estratégia para ignorar conflitos de chaves duplicadas
    if tipo_conflito == "nada":
        stmt = stmt.on_conflict_do_nothing()
    # Configura a estratégia de upsert (se houver conflito, atualiza os campos definidos)
    elif tipo_conflito == "atualizar" and chave_conflito and colunas_update:
        stmt = stmt.on_conflict_do_update(
            index_elements=chave_conflito,
            set_={col: getattr(stmt.excluded, col) for col in colunas_update},
        )
    # Retorna erro se a configuração do método de conflito estiver incorreta
    else:
        raise ValueError(f"Tipo de conflito inválido: {tipo_conflito}")

    # Executa a query final passando a lista de registros estruturados
    conn.execute(stmt, linhas)

    # Obtém a contagem de registros após a inserção
    contador_depois = _contar_registros(conn, tabela_nome)
    # Calcula quantas linhas foram de fato adicionadas de forma líquida
    inseridos = contador_depois - contador_antes

    # Retorna o total lido e o saldo líquido de novos registros no banco de dados
    return total_processado, max(inseridos, 0)


def ingerir_movielens(diretorio_dados: Path) -> dict[str, int]:
    """Executa o pipeline completo de ingestão: lê todos os CSVs e grava no PostgreSQL de forma idempotente.

    Toda a execução ocorre dentro de uma única transação de banco de dados.
    """
    # Registra no log o início de toda a rotina
    logger.info("Iniciando ingestão do MovieLens a partir de %s", diretorio_dados)

    # Obtém a instância do mecanismo de conexão (Engine) do banco de dados
    engine: Engine = get_engine()
    # Inicializa os acumuladores globais de estatísticas
    total_processado = 0
    total_inserido = 0

    # Inicia o bloco de transação segura. Ao fim dele, se não houver erros, envia um COMMIT.
    with engine.begin() as conn:
        # Cria um novo lote na tabela de auditoria para esta execução
        batch_id = _criar_batch(conn, "movielens")

        try:
            # 1. Processamento da tabela de filmes (movies)
            arquivo_movies = diretorio_dados / "movies.csv"
            if arquivo_movies.exists():
                # Executa a inserção do CSV com lógica de Upsert na chave composta
                proc, ins = _ingest_arquivo(
                    conn,
                    arquivo_movies,
                    "movies",
                    ["movie_id", "title", "genres"],
                    tipo_conflito="atualizar",
                    chave_conflito=["movie_id"],
                    colunas_update=["title", "genres"],
                )
                # Acumula o progresso
                total_processado += proc
                total_inserido += ins
                logger.info("movies: processados=%s inseridos=%s", proc, ins)

            # 2. Processamento da tabela de links (links)
            arquivo_links = diretorio_dados / "links.csv"
            if arquivo_links.exists():
                # Executa a inserção dos links também com lógica de Upsert
                proc, ins = _ingest_arquivo(
                    conn,
                    arquivo_links,
                    "links",
                    ["movie_id", "imdb_id", "tmdb_id"],
                    tipo_conflito="atualizar",
                    chave_conflito=["movie_id"],
                    colunas_update=["imdb_id", "tmdb_id"],
                )
                # Acumula o progresso
                total_processado += proc
                total_inserido += ins
                logger.info("links: processados=%s inseridos=%s", proc, ins)

            # 3. Processamento das avaliações (ratings)
            arquivo_ratings = diretorio_dados / "ratings.csv"
            if arquivo_ratings.exists():
                # Executa inserção ignorando duplicados (nada a atualizar nas avaliações históricas)
                proc, ins = _ingest_arquivo(
                    conn,
                    arquivo_ratings,
                    "ratings",
                    ["user_id", "movie_id", "rating", "ts"],
                    tipo_conflito="nada",
                )
                # Acumula o progresso
                total_processado += proc
                total_inserido += ins
                logger.info("ratings: processados=%s inseridos=%s", proc, ins)

            # 4. Processamento das tags (tags)
            arquivo_tags = diretorio_dados / "tags.csv"
            if arquivo_tags.exists():
                # Executa a inserção ignorando duplicados
                proc, ins = _ingest_arquivo(
                    conn,
                    arquivo_tags,
                    "tags",
                    ["user_id", "movie_id", "tag", "ts"],
                    tipo_conflito="nada",
                )
                # Acumula o progresso
                total_processado += proc
                total_inserido += ins
                logger.info("tags: processados=%s inseridos=%s", proc, ins)

            # Se todos os arquivos passaram sem exceção, atualiza o status do lote para "success"
            _finalizar_batch(
                conn,
                batch_id,
                "success",
                rows_processed=total_processado,
                rows_inserted=total_inserido,
                rows_updated=0,
            )
            logger.info("Ingestão concluída com sucesso. Batch %s", batch_id)

        except Exception as exc:
            # Caso aconteça um erro (ex: falha de disco, de rede ou dados corrompidos),
            # grava a exceção nos logs e atualiza o status do lote para "failed" no banco.
            logger.exception("Erro durante a ingestão do MovieLens")
            _finalizar_batch(
                conn,
                batch_id,
                "failed",
                rows_processed=total_processado,
                rows_inserted=total_inserido,
                error_message=str(exc),
            )
            # Propaga o erro para invalidar a transação ativa e disparar o Rollback automático
            raise

    # Retorna o dicionário de resultados finais consolidados
    return {
        "batch_id": batch_id,
        "rows_processed": total_processado,
        "rows_inserted": total_inserido,
    }
