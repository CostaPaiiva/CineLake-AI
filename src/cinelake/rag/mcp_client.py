"""Cliente MCP via HTTP."""

import logging
from typing import Any

import httpx

from cinelake.config import settings

logger = logging.getLogger(__name__)


def invocar_ferramenta_mcp(nome_ferramenta: str, argumentos: dict[str, Any] | None = None) -> Any:
    """Chama uma ferramenta MCP via HTTP."""
    url = f"{settings.mcp_base_url}/tools/{nome_ferramenta}"
    headers = {"Authorization": f"Bearer {settings.mcp_token}"}
    payload = {"argumentos": argumentos or {}}

    try:
        with httpx.Client(timeout=30) as client:
            resposta = client.post(url, json=payload, headers=headers)
            resposta.raise_for_status()
            return resposta.json()["resultado"]
    except Exception as exc:
        logger.error("Erro ao invocar %s: %s", nome_ferramenta, exc)
        raise
