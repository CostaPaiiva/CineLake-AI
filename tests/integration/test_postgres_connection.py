"""Testes de integração para a conexão com o PostgreSQL."""

import pytest

from sqlalchemy import text
from cinelake.db import check_database_connection, get_engine


@pytest.mark.integration
def test_database_connection() -> None:
    """Testa se conseguimos nos conectar ao PostgreSQL e executar uma consulta simples."""
    # Garante que a função de checagem do banco retorne True
    assert check_database_connection() is True


@pytest.mark.integration
def test_service_heartbeat_table_exists() -> None:
    """Testa se as migrações foram aplicadas e a tabela service_heartbeat existe."""
    # Obtém a engine de conexão do banco de dados
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Consulta o Postgres para verificar se a tabela existe no schema público
            result = conn.execute(
                text("SELECT to_regclass('public.service_heartbeat')")
            ).scalar()
            # Garante que o retorno do banco de dados seja o próprio nome da tabela, confirmando sua existência
            assert result == "service_heartbeat"
    finally:
        # Garante que a engine de conexão do teste seja encerrada de forma limpa
        engine.dispose()