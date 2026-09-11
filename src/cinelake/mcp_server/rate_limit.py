"""Rate limiting simples em memória."""

import logging
import time
from collections import defaultdict

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Limite por token: 60 requisições por minuto
LIMITE = 60
JANELA_SEGUNDOS = 60

_historico: dict[str, list[float]] = defaultdict(list)


def verificar_rate_limit(token_name: str) -> None:
    """Verifica se o token excedeu o limite de requisições."""
    agora = time.time()
    historico = _historico[token_name]
    # Remove requisições antigas
    historico[:] = [t for t in historico if agora - t < JANELA_SEGUNDOS]
    if len(historico) >= LIMITE:
        logger.warning("Rate limit excedido para %s", token_name)
        raise HTTPException(status_code=429, detail="Rate limit excedido")
    historico.append(agora)
