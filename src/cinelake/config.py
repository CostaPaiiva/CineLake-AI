"""Configurações globais da aplicação carregadas a partir de variáveis de ambiente (.env)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Define o caminho raiz absoluto do projeto subindo 2 níveis na árvore de diretórios
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Objeto imutável de configurações para garantir consistência em toda a aplicação."""

    project_name: str
    environment: str
    log_level: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    database_url: str
    tmdb_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega e valida as configurações a partir do arquivo .env e variáveis do sistema."""
        # Carrega o arquivo .env localizado na raiz do projeto
        load_dotenv(PROJECT_ROOT / ".env")

        # Configurações do PostgreSQL com valores padrão para desenvolvimento
        user = os.getenv("POSTGRES_USER", "cinelake")
        password = os.getenv("POSTGRES_PASSWORD", "cinelake_password")
        db = os.getenv("POSTGRES_DB", "cinelake")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))

        # Constrói a URL do SQLAlchemy caso DATABASE_URL não tenha sido informada explicitamente
        database_url = os.getenv(
            "DATABASE_URL",
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}",
        )
        # Chave de autenticação na API do TMDb
        tmdb_api_key = os.getenv("TMDB_API_KEY", "")

        # Retorna a instância preenchida e tipada
        return cls(
            project_name="CineLake AI",
            environment=os.getenv("CINELAKE_ENV", "development"),
            log_level=os.getenv("CINELAKE_LOG_LEVEL", "INFO"),
            postgres_user=user,
            postgres_password=password,
            postgres_db=db,
            postgres_host=host,
            postgres_port=port,
            database_url=database_url,
            tmdb_api_key=tmdb_api_key,
        )


# Instância singleton global de configurações para importação direta em outros módulos
settings = Settings.from_env()
