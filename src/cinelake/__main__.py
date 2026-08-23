"""Ponto de entrada da CLI para o CineLake AI."""

import argparse
import logging

from cinelake.config import settings
from cinelake.db import check_database_connection
from cinelake.logging_config import setup_logging


def main() -> None:
    """Executa um teste básico ('smoke test') e inicializa o CineLake AI."""
    # Configura o nível de logs com base nas configurações (ex: INFO, DEBUG, WARN)
    setup_logging(settings.log_level)

    # Configura o analisador de argumentos passados via terminal
    parser = argparse.ArgumentParser(description="CineLake AI CLI")

    # Adiciona a flag opcional '--check-db' para testar a conexão com o banco
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Check database connectivity",
    )
    args = parser.parse_args()

    # Obtém a instância do logger para este arquivo
    logger = logging.getLogger(__name__)
    logger.info(
        "CineLake AI initialized",
        extra={"environment": settings.environment},
    )

    # Se a flag '--check-db' foi informada ao rodar a CLI
    if args.check_db:
        logger.info("Checking database connection...")
        ok = check_database_connection()
        if ok:
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
            # Encerra o script com código de erro 1 se a conexão falhar
            raise SystemExit(1)


# Garante que o método main() só roda se o arquivo for executado diretamente (ex: python -m cinelake)
if __name__ == "__main__":
    main()
