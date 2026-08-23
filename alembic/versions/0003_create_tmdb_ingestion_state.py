"""Cria a tabela de estado da ingestão TMDb para controle de checkpoint.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-23

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores de revisão do Alembic para controle de versão do banco
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela tmdb_ingestion_state e inicializa o registro inicial de checkpoint."""
    # Criação da tabela que armazena o cursor/estado da ingestão incremental da API do TMDb
    op.create_table(
        "tmdb_ingestion_state",
        # ID fixo do estado (usado como registro singleton com ID 1)
        sa.Column("id", sa.Integer(), primary_key=True),
        # Último movie_id processado com sucesso para continuar a partir dele
        sa.Column(
            "last_processed_movie_id",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        # Data/hora em que a última execução ocorreu
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamp de atualização automática do registro no banco
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Insere o registro inicial padrão (id=1, last_processed_movie_id=0)
    op.execute(
        "INSERT INTO tmdb_ingestion_state (id, last_processed_movie_id) VALUES (1, 0)"
    )


def downgrade() -> None:
    """Remove a tabela tmdb_ingestion_state em caso de rollback."""
    op.drop_table("tmdb_ingestion_state")
