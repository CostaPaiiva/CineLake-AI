"""Ferramentas de saúde da plataforma integradas ao Servidor MCP."""

import logging

from mcp.server.fastmcp import FastMCP

from cinelake.observability.health import coletar_status_geral, obter_ultimas_execucoes

logger = logging.getLogger(__name__)


def registrar_ferramentas(server: FastMCP) -> None:
    """Registra as ferramentas de consulta de saúde da plataforma no servidor MCP.

    Args:
        server: Instância do servidor MCP onde as ferramentas serão registradas.
    """

    @server.tool("get_platform_health")
    async def get_platform_health() -> str:
        """Retorna o status geral de saúde da plataforma (conectividade e contagens)."""
        status = coletar_status_geral()
        return str(status)

    @server.tool("get_data_freshness")
    async def get_data_freshness() -> str:
        """Retorna a frescura (freshness) dos dados por fonte de ingestão em minutos."""
        freshness = obter_ultimas_execucoes()
        return str(freshness)
