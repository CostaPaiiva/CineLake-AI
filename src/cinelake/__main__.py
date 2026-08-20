"""Ponto de entrada da CLI para o CineLake AI."""

import logging

from cinelake.config import settings
from cinelake.logging_config import setup_logging


def main() -> None:
    """Executa o teste básico de fumaça (smoke test) de fundação do CineLake AI."""
    # Configura o sistema de logging com base no nível definido nas configurações
    setup_logging(settings.log_level)

    # Inicializa o logger para o módulo atual
    logger = logging.getLogger(__name__)
    logger.info(
        "CineLake AI inicializado",
        extra={"environment": settings.environment},
    )


if __name__ == "__main__":
    # Executa a função principal se o script for executado diretamente
    main()