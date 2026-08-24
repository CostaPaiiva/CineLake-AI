"""Configurações da aplicação carregadas a partir de variáveis de ambiente."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# Define o diretório raiz do projeto (PROJECT_ROOT) subindo 2 níveis a partir deste arquivo (src/cinelake/config.py)
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
    tmdb_api_key: str
    minio_access_key: str
    minio_secret_key: str
    minio_endpoint: str
    minio_bucket: str
    minio_use_ssl: bool

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega as configurações a partir do arquivo .env e variáveis de ambiente."""
        # Carrega as variáveis do arquivo .env localizado na raiz do projeto
        load_dotenv(PROJECT_ROOT / ".env")

        # Configurações do PostgreSQL com valores padrão (fallback) caso não estejam no ambiente
        user = os.getenv("POSTGRES_USER", "cinelake")
        password = os.getenv("POSTGRES_PASSWORD", "cinelake_password")
        db = os.getenv("POSTGRES_DB", "cinelake")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        
        # Constrói a URL do banco caso DATABASE_URL não esteja explicitamente configurada
        database_url = os.getenv(
            "DATABASE_URL",
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}",
        )
        
        # Chave da API do TMDB
        tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        
        # Configurações do MinIO com valores padrão (fallback) caso não estejam no ambiente
        minio_access_key = os.getenv("MINIO_ACCESS_KEY", "cinelake_minio")
        minio_secret_key = os.getenv("MINIO_SECRET_KEY", "cinelake_minio_secret")
        minio_endpoint = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
        minio_bucket = os.getenv("MINIO_BUCKET", "data-lake")
        
        # Converte a string do SSL para um valor booleano Python (True/False)
        minio_use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

        # Retorna a instância da classe Settings populada com todas as configurações
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
            minio_access_key=minio_access_key,
            minio_secret_key=minio_secret_key,
            minio_endpoint=minio_endpoint,
            minio_bucket=minio_bucket,
            minio_use_ssl=minio_use_ssl,
        )


# Cria uma instância única global das configurações para ser importada e usada por todo o projeto
settings = Settings.from_env()