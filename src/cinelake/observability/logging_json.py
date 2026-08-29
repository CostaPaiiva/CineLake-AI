"""Configuração de logging estruturado em JSON."""

import logging
import sys

import pythonjsonlogger.jsonlogger  # type: ignore[import-untyped]


def setup_json_logging(level: str = "INFO") -> None:
    """Configura logging estruturado com saída em formato JSON no stdout.

    Args:
        level: Nível do log (DEBUG, INFO, WARNING, ERROR, CRITICAL). Padrão 'INFO'.
    """
    # Handler para direcionar a saída dos logs para a saída padrão (stdout)
    handler = logging.StreamHandler(sys.stdout)

    # Formatador JSON contendo data/hora, nível do log, nome do logger e mensagem
    formatter = pythonjsonlogger.jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    # Configuração global do serviço de logs do Python
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler])
