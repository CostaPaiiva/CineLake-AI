"""cria tabela rag_documents com pgvector

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


class VECTOR(sa.types.UserDefinedType):
    """Tipo customizado para representar a extensão pgvector de 384 dimensões."""

    def get_col_spec(self, **kw: object) -> str:
        """Retorna a especificação DDL SQL para a coluna de tipo vetor."""
        return "VECTOR(384)"


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Habilita a extensão pgvector e cria a tabela `rag_documents`."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("fonte", sa.Text(), nullable=False),
        sa.Column("metadados", JSONB(), nullable=True),
        sa.Column("embedding", VECTOR(), nullable=True),
        sa.Column("source_id", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove a tabela `rag_documents` e desabilita a extensão vector."""
    op.drop_table("rag_documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
