"""Cria a tabela service_heartbeat

Revision ID: 0001
Revises: None (Esta é a migração inicial)
Create Date: 2026-08-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores únicos da migração no histórico do Alembic
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica a migração para criar a tabela 'service_heartbeat' no banco de dados.
    
    A tabela conterá as seguintes colunas:
    - id: Inteiro, chave primária com auto-incremento.
    - service_name: Texto (tamanho máx 100), obrigatório (não nulo).
    - heartbeat_at: Data e hora com fuso horário (timezone=True), preenchido automaticamente pelo banco com a hora atual.
    """
    op.create_table(
        "service_heartbeat",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Desfaz a migração removendo (dropando) a tabela 'service_heartbeat' do banco de dados.
    """
    op.drop_table("service_heartbeat")