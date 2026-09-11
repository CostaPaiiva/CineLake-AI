"""Autenticação por token Bearer para o servidor MCP."""

import logging

from fastapi import Header, HTTPException

from cinelake.config import settings

logger = logging.getLogger(__name__)


async def verificar_token(authorization: str | None = Header(default=None)) -> str:
    """
    Verifica se o cabeçalho Authorization contém um token válido.

    Retorna o nome do token (para auditoria).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")

    partes = authorization.split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato de token inválido")

    token = partes[1]
    if token != settings.mcp_token:
        logger.warning("Tentativa de acesso com token inválido")
        raise HTTPException(status_code=401, detail="Token inválido")

    return "default"
