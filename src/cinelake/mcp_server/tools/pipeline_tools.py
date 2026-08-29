"""Ferramentas de auditoria e status de pipelines registradas no Servidor MCP."""

import logging

from mcp.server import Server
from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def registrar_ferramentas(server: Server) -> None:
    """Registra as ferramentas de consulta e detalhamento de pipelines de dados no servidor MCP.

    Args:
        server: Instância do servidor MCP onde as ferramentas serão registradas.
    """

    @server.tool("get_pipeline_status")
    async def get_pipeline_status(source: str | None = None) -> str:
        """Retorna o histórico de execuções de pipelines, com filtro opcional por fonte de dados."""
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
            resultados = []
            for linha in linhas:
                resultados.append(
                    {
                        "batch_id": linha[0],
                        "source": linha[1],
                        "status": linha[2],
                        "started_at": linha[3].isoformat() if linha[3] else None,
                        "finished_at": linha[4].isoformat() if linha[4] else None,
                        "rows_processed": linha[5],
                        "rows_inserted": linha[6],
                    }
                )
        return str(resultados)

    @server.tool("list_failed_pipelines")
    async def list_failed_pipelines(limit: int = 10) -> str:
        """Lista as últimas execuções de pipeline que terminaram com status de falha/erro."""
        engine = get_engine()
        with engine.connect() as conn:
            linhas = conn.execute(
                text(
                    """
                    SELECT batch_id, source, status, started_at, finished_at, error_message
                    FROM ingestion_batch
                    WHERE status = 'failed'
                    ORDER BY started_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).fetchall()
            resultados = []
            for linha in linhas:
                resultados.append(
                    {
                        "batch_id": linha[0],
                        "source": linha[1],
                        "status": linha[2],
                        "started_at": linha[3].isoformat() if linha[3] else None,
                        "finished_at": linha[4].isoformat() if linha[4] else None,
                        "error_message": linha[5],
                    }
                )
        return str(resultados)

    @server.tool("get_pipeline_run")
    async def get_pipeline_run(batch_id: int) -> str:
        """Retorna os detalhes completos de auditoria de uma execução específica pelo batch_id."""
        engine = get_engine()
        with engine.connect() as conn:
            linha = conn.execute(
                text(
                    """
                    SELECT batch_id, source, status, started_at, finished_at,
                           rows_processed, rows_inserted, rows_updated, error_message
                    FROM ingestion_batch
                    WHERE batch_id = :batch_id
                    """
                ),
                {"batch_id": batch_id},
            ).fetchone()
            if not linha:
                return f"Batch {batch_id} não encontrado."
            resultado = {
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
        return str(resultado)

