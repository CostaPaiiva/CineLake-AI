# Módulo de carregamento e gerenciamento de configurações da aplicação a partir de variáveis de ambiente
"""Configurações da aplicação carregadas a partir de variáveis de ambiente."""

# Importação do módulo os da biblioteca padrão para leitura de variáveis de ambiente do sistema
import os
# Importação do decorador dataclass para criação de classes de dados estruturadas
from dataclasses import dataclass
# Importação da classe Path do módulo pathlib para manipulação e resolução de caminhos de arquivos
from pathlib import Path

# Importação da função load_dotenv para carregar variáveis a partir de arquivos .env
from dotenv import load_dotenv

# Define o diretório raiz do projeto (PROJECT_ROOT) subindo 2 níveis a partir deste arquivo (src/cinelake/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# Decorador dataclass com frozen=True torna os atributos da classe imutáveis após a instanciação
@dataclass(frozen=True)
class Settings:
    """Objeto de configuração imutável (frozen=True) para a aplicação."""

    # Nome identificador do projeto
    project_name: str
    # Ambiente de execução atual (development, production, testing)
    environment: str
    # Nível de logging da aplicação (INFO, DEBUG, ERROR, etc.)
    log_level: str
    # Nome do usuário administrador do PostgreSQL
    postgres_user: str
    # Senha de autenticação do usuário do PostgreSQL
    postgres_password: str
    # Nome do banco de dados principal no PostgreSQL
    postgres_db: str
    # Endereço de host para conexão com o PostgreSQL
    postgres_host: str
    # Porta de comunicação da instância do PostgreSQL
    postgres_port: int
    # String/URI completa de conexão SQLAlchemy com o PostgreSQL
    database_url: str
    # Chave de API de autenticação para os serviços do TMDB
    tmdb_api_key: str
    # Chave de acesso root/usuário do serviço MinIO (S3)
    minio_access_key: str
    # Chave secreta de autenticação do serviço MinIO (S3)
    minio_secret_key: str
    # Endereço de host e porta do endpoint da API do MinIO
    minio_endpoint: str
    # Nome do bucket padrão de armazenamento de dados no MinIO
    minio_bucket: str
    # Indicador se a comunicação com o MinIO deve utilizar HTTPS (True) ou HTTP (False)
    minio_use_ssl: bool
    # URI de rastreamento do servidor MLflow
    mlflow_tracking_uri: str
    # Endpoint do servidor S3 (MinIO) utilizado pelo MLflow para salvar artefatos
    mlflow_s3_endpoint_url: str
    # Flag para ignorar validação de certificados SSL/TLS no S3 para o MLflow
    mlflow_s3_ignore_tls: bool
    # Nome do bucket padrão no MinIO destinado aos artefatos do MLflow
    mlflow_artifact_bucket: str

    # Método de classe para instanciar as configurações lendo os valores das variáveis de ambiente
    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega as configurações a partir do arquivo .env e variáveis de ambiente."""
        # Carrega as variáveis do arquivo .env localizado na raiz do projeto garantindo a substituição com override=True
        load_dotenv(PROJECT_ROOT / ".env", override=True)

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

        # Configurações do MLflow com valores padrão (fallback) caso não estejam configuradas no ambiente
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
        mlflow_s3_endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://127.0.0.1:9000")
        mlflow_s3_ignore_tls = os.getenv("MLFLOW_S3_IGNORE_TLS", "true").lower() == "true"
        mlflow_artifact_bucket = os.getenv("MLFLOW_ARTIFACT_BUCKET", "mlflow-artifacts")

        # Retorna a instância da classe Settings populada com todas as configurações lidas
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
            mlflow_tracking_uri=mlflow_tracking_uri,
            mlflow_s3_endpoint_url=mlflow_s3_endpoint_url,
            mlflow_s3_ignore_tls=mlflow_s3_ignore_tls,
            mlflow_artifact_bucket=mlflow_artifact_bucket,
        )


# Cria uma instância única global das configurações para ser importada e usada por todo o projeto
settings = Settings.from_env()
