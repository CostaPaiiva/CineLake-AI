"""Servidor MCP principal do CineLake AI para comunicação via entrada/saída padrão (stdio)."""

import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from cinelake.mcp_server.tools import (
    health_tools,
    pipeline_tools,
    quality_tools,
    schema_tools,
)

logger = logging.getLogger(__name__)


def criar_servidor() -> Server:
    """Cria e inicializa o servidor MCP integrando todos os conjuntos de ferramentas (tools) da plataforma.

    Returns:
        Server: Instância configurada do servidor MCP com os módulos de saúde, pipelines, qualidade e esquemas.
    """
    app = Server("cinelake-mcp")

    # Registra todos os grupos de ferramentas de observabilidade e dados
    health_tools.registrar_ferramentas(app)
    pipeline_tools.registrar_ferramentas(app)
    quality_tools.registrar_ferramentas(app)
    schema_tools.registrar_ferramentas(app)

    return app


async def executar_servidor() -> None:
    """Executa o loop de eventos assíncrono do servidor MCP utilizando o transporte via stdio (estrada/saída padrão)."""
    app = criar_servidor()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


# Ponto de entrada padrão para execução direta do script via Python
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(executar_servidor())
