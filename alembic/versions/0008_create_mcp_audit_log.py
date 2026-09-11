"""cria tabela mcp_audit_log

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-11

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria tabela de auditoria de chamadas MCP."""
    op.create_table(
        "mcp_audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("token_name", sa.Text(), nullable=True),
        sa.Column("tool_name", sa.Text(), nullable=False),
        sa.Column("arguments", JSONB(), nullable=True),
        sa.Column("result_status", sa.Text(), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Remove a tabela mcp_audit_log."""
    op.drop_table("mcp_audit_log")
