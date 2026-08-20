"""Configurações da aplicação carregadas a partir de variáveis de ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Define o diretório raiz do projeto (PROJECT_ROOT) retrocedendo dois níveis a partir deste arquivo
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Objeto de configurações imutável (frozen) para a aplicação."""

    # Nome do projeto
    project_name: str
    # Ambiente de execução (ex: development, production)
    environment: str
    # Nível de log (ex: INFO, DEBUG, WARNING)
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega as configurações a partir do arquivo .env e variáveis de ambiente."""
        # Carrega o arquivo .env localizado na raiz do projeto
        load_dotenv(PROJECT_ROOT / ".env")

        return cls(
            project_name="CineLake AI",
            # Obtém a variável de ambiente CINELAKE_ENV, com valor padrão 'development'
            environment=os.getenv("CINELAKE_ENV", "development"),
            # Obtém a variável de ambiente CINELAKE_LOG_LEVEL, com valor padrão 'INFO'
            log_level=os.getenv("CINELAKE_LOG_LEVEL", "INFO"),
        )


# Instância global das configurações carregadas para fácil importação em outros módulos
settings = Settings.from_env()
