"""Engine do banco de dados e funções de conexão."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from cinelake.config import settings


def get_engine() -> Engine:
    """Cria e retorna a Engine do SQLAlchemy utilizando a URL do banco configurada.

    Parâmetros:
    - pool_pre_ping=True: Verifica a saúde da conexão (com um teste simples de "ping") antes
      de entregá-la ao código, reconectando automaticamente se o banco tiver caído/reiniciado.
    - future=True: Habilita o estilo de uso moderno compatível com a API do SQLAlchemy 2.0.
    """
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )


def check_database_connection() -> bool:
    """Realiza um teste simples de conexão com o banco de dados.

    Executa a query mínima 'SELECT 1' para certificar que o banco está ativo e acessível.
    Retorna True em caso de sucesso e garante que os recursos de conexão sejam liberados
    ao rodar o 'engine.dispose()' no bloco 'finally'.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    finally:
        engine.dispose()
