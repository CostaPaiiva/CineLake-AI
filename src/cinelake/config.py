"""Configurações da aplicação carregadas a partir de variáveis de ambiente (.env)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Define a raiz do projeto subindo dois diretórios a partir deste arquivo (src/cinelake/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Objeto de configuração imutável (frozen=True) para a aplicação."""

    project_name: str
    environment: str
    log_level: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega as configurações a partir das variáveis de ambiente e do arquivo .env."""
        # Carrega o arquivo .env localizado na raiz do projeto
        load_dotenv(PROJECT_ROOT / ".env")

        # Recupera as variáveis do banco de dados com valores padrão caso não estejam no .env
        user = os.getenv("POSTGRES_USER", "cinelake")
        password = os.getenv("POSTGRES_PASSWORD", "cinelake_password")
        db = os.getenv("POSTGRES_DB", "cinelake")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))

        # Constrói a URL do banco SQLAlchemy usando os dados anteriores se DATABASE_URL não estiver definida
        database_url = os.getenv(
            "DATABASE_URL",
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}",
        )

        # Retorna a instância do Settings preenchida
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
        )


# Instância global de configurações para ser importada em outros módulos do projeto
settings = Settings.from_env()
