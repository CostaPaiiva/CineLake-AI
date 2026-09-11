"""Registro de auditoria das chamadas MCP."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def registrar_chamada(
    tool_name: str,
    argumentos: dict[str, Any],
    token_name: str,
    status: str,
    execution_time_ms: float,
    error_message: str | None = None,
) -> None:
    """Registra chamada na tabela mcp_audit_log."""
    engine = get_engine()
    request_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO mcp_audit_log
                    (request_id, token_name, tool_name, arguments, result_status, execution_time_ms, error_message, created_at)
                VALUES
                    (:request_id, :token_name, :tool_name, :args, :status, :exec_time, :error, :agora)
            """),
            {
                "request_id": request_id,
                "token_name": token_name,
                "tool_name": tool_name,
                "args": json.dumps(argumentos) if isinstance(argumentos, dict) else argumentos,
                "status": status,
                "exec_time": execution_time_ms,
                "error": error_message,
                "agora": datetime.now(timezone.utc),
            },
        )
