"""Ferramentas de inspeção de esquema (schema) e linhagem de dados no Servidor MCP."""

import logging

from mcp.server.fastmcp import FastMCP
from sqlalchemy import inspect

from cinelake.db import get_engine

logger = logging.getLogger(__name__)

# Mapeamento simplificado de linhagem de dados (dependências dbt)
LINHAGEM: dict[str, list[str]] = {
    "dim_movie": ["stg_movies", "movies"],
    "dim_user": ["stg_ratings", "ratings"],
    "fact_rating": ["stg_ratings", "dim_date", "dim_movie", "dim_user"],
    "stg_movies": ["movies"],
    "stg_ratings": ["ratings"],
}


def registrar_ferramentas(server: FastMCP) -> None:
    """Registra as ferramentas de consulta de esquema de tabela e linhagem de dados no servidor MCP.

    Args:
        server: Instância do servidor MCP onde as ferramentas serão registradas.
    """

    @server.tool("get_table_schema")
    async def get_table_schema(tabela: str) -> str:
        """Retorna o esquema (colunas e tipos) de uma tabela do banco de dados."""
        engine = get_engine()
        try:
            with engine.connect() as conn:
                insp = inspect(conn)
                colunas = insp.get_columns(tabela)
                resultado = [
                    {"coluna": col["name"], "tipo": str(col["type"])}
                    for col in colunas
                ]
            return str(resultado)
        except Exception as exc:
            logger.error("Erro ao obter esquema da tabela %s: %s", tabela, exc)
            return f"Erro: {exc}"

    @server.tool("get_table_lineage")
    async def get_table_lineage(tabela: str) -> str:
        """Retorna a linhagem e as dependências upstream de dados de uma determinada tabela."""
        linhagem = LINHAGEM.get(tabela)
        if linhagem:
            return f"Tabela: {tabela}\nDependências: {linhagem}"
        return f"Tabela {tabela} não possui linhagem definida."
