"""Configurações de logging para o CineLake AI."""

import logging
import sys


def setup_logging(log_level: str) -> None:
    """Configura o logger padrão da aplicação."""
    # Converte o nível de texto (ex: "INFO") para o valor numérico correspondente do módulo logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
