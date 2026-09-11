"""Servidor MCP remoto via HTTP (FastAPI)."""

import logging
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from cinelake.mcp_server import tools
from cinelake.mcp_server.audit import registrar_chamada
from cinelake.mcp_server.auth import verificar_token
from cinelake.mcp_server.rate_limit import verificar_rate_limit

logger = logging.getLogger(__name__)

app = FastAPI(title="CineLake MCP Server (remoto)", version="1.0.0")


class ToolRequest(BaseModel):
    argumentos: dict[str, Any] = {}


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck do servidor MCP."""
    return {"status": "ok"}


@app.post("/tools/{tool_name}")
def executar_tool(
    tool_name: str,
    body: ToolRequest,
    token_name: str = Depends(verificar_token),
) -> dict[str, Any]:
    """Executa uma ferramenta MCP autenticada."""
    verificar_rate_limit(token_name)
    if not hasattr(tools, tool_name):
        raise HTTPException(status_code=404, detail=f"Ferramenta {tool_name} não encontrada")

    funcao = getattr(tools, tool_name)
    inicio = time.time()
    status = "success"
    erro = None
    try:
        resultado = funcao(**body.argumentos)
    except Exception as exc:
        status = "error"
        erro = str(exc)
        logger.exception("Erro ao executar %s", tool_name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        exec_ms = (time.time() - inicio) * 1000
        try:
            registrar_chamada(
                tool_name=tool_name,
                argumentos=body.argumentos,
                token_name=token_name,
                status=status,
                execution_time_ms=exec_ms,
                error_message=erro,
            )
        except Exception as log_exc:
            logger.error("Falha ao auditar chamada MCP: %s", log_exc)

    return {"tool": tool_name, "resultado": resultado}
