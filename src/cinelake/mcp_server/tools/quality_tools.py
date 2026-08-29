"""Ferramentas de qualidade de dados integradas ao Servidor MCP."""

import logging

from mcp.server import Server
from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def registrar_ferramentas(server: Server) -> None:
    """Registra as ferramentas de consulta de qualidade de dados no servidor MCP.

    Args:
        server: Instância do servidor MCP onde as ferramentas serão registradas.
    """

    @server.tool("get_data_quality_failures")
    async def get_data_quality_failures(limit: int = 10) -> str:
        """Retorna falhas de validação de qualidade de dados (baseado em checkpoints do Great Expectations ou registros de falhas)."""
        # Consulta os registros de falha na ingestão para identificar problemas de qualidade
        engine = get_engine()
        with engine.connect() as conn:
            linhas = conn.execute(
                text(
                    """
                    SELECT batch_id, source, error_message, finished_at
                    FROM ingestion_batch
                    WHERE status = 'failed'
                    ORDER BY finished_at DESC
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
                        "error_message": linha[2],
                        "finished_at": linha[3].isoformat() if linha[3] else None,
                    }
                )
        return str(resultados)
