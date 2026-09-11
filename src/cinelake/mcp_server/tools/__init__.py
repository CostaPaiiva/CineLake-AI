"""Ferramentas MCP do CineLake AI."""

from typing import Any

from sqlalchemy import inspect, text

from cinelake.db import get_engine
from cinelake.observability.health import coletar_status_geral, obter_ultimas_execucoes


def get_platform_health() -> dict[str, Any]:
    """Retorna o status geral de saúde da plataforma."""
    return coletar_status_geral()


def get_data_freshness() -> dict[str, Any]:
    """Retorna a frescura dos dados por fonte."""
    return obter_ultimas_execucoes()


def get_pipeline_status(source: str | None = None) -> list[dict[str, Any]]:
    """Retorna histórico de execuções de pipelines."""
    engine = get_engine()
    query = (
        "SELECT batch_id, source, status, started_at, finished_at, rows_processed, rows_inserted "
        "FROM ingestion_batch"
    )
    params = {}
    if source:
        query += " WHERE source = :source"
        params["source"] = source
    query += " ORDER BY started_at DESC LIMIT 50"

    with engine.connect() as conn:
        linhas = conn.execute(text(query), params).fetchall()
        return [
            {
                "batch_id": r[0],
                "source": r[1],
                "status": r[2],
                "started_at": r[3].isoformat() if r[3] else None,
                "finished_at": r[4].isoformat() if r[4] else None,
                "rows_processed": r[5],
                "rows_inserted": r[6],
            }
            for r in linhas
        ]


def list_failed_pipelines(limit: int = 10) -> list[dict[str, Any]]:
    """Lista execuções de pipelines que falharam."""
    engine = get_engine()
    with engine.connect() as conn:
        linhas = conn.execute(
            text(
                "SELECT batch_id, source, status, started_at, finished_at, error_message "
                "FROM ingestion_batch WHERE status = 'failed' ORDER BY started_at DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()
        return [
            {
                "batch_id": r[0],
                "source": r[1],
                "status": r[2],
                "started_at": r[3].isoformat() if r[3] else None,
                "finished_at": r[4].isoformat() if r[4] else None,
                "error_message": r[5],
            }
            for r in linhas
        ]


def get_pipeline_run(batch_id: int) -> dict[str, Any] | str:
    """Retorna detalhes de uma execução de pipeline."""
    engine = get_engine()
    with engine.connect() as conn:
        linha = conn.execute(
            text(
                "SELECT batch_id, source, status, started_at, finished_at, "
                "rows_processed, rows_inserted, rows_updated, error_message "
                "FROM ingestion_batch WHERE batch_id = :batch_id"
            ),
            {"batch_id": batch_id},
        ).fetchone()
        if not linha:
            return f"Batch {batch_id} não encontrado."
        return {
            "batch_id": linha[0],
            "source": linha[1],
            "status": linha[2],
            "started_at": linha[3].isoformat() if linha[3] else None,
            "finished_at": linha[4].isoformat() if linha[4] else None,
            "rows_processed": linha[5],
            "rows_inserted": linha[6],
            "rows_updated": linha[7],
            "error_message": linha[8],
        }


def get_table_schema(tabela: str = "movies") -> list[dict[str, str]]:
    """Retorna colunas e tipos de uma tabela."""
    engine = get_engine()
    with engine.connect() as conn:
        insp = inspect(conn)
        colunas = insp.get_columns(tabela)
        return [{"coluna": col["name"], "tipo": str(col["type"])} for col in colunas]


def get_table_lineage(tabela: str = "movies") -> dict[str, Any]:
    """Retorna a linhagem de uma tabela."""
    return {"tabela": tabela, "linhagem": []}


def get_lineage(tabela: str) -> dict[str, Any]:
    """Linhagem básica (placeholder)."""
    return {"tabela": tabela, "linhagem": []}


def get_data_quality_failures() -> list[dict[str, Any]]:
    """Retorna falhas recentes de qualidade de dados."""
    return []
