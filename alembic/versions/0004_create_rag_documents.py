"""Cria tabela rag_documents com suporte a extensão pgvector para busca vetorial RAG.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-29

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType

# Identificadores de revisão do Alembic
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class VECTOR(UserDefinedType):
    """Tipo de dado customizado para colunas vetoriais do pgvector no PostgreSQL."""

    def get_col_spec(self, **kw: object) -> str:
        """Retorna a especificação DDL SQL para o vetor de 384 dimensões."""
        return "VECTOR(384)"


def upgrade() -> None:
    """Habilita a extensão pgvector no PostgreSQL e cria a tabela `rag_documents`."""
    # Habilita a extensão pgvector para permitir operações de busca por similaridade vetorial
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Cria a tabela de documentos e embeddings para o pipeline RAG
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
