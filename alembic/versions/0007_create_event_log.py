# Docstring do módulo descrevendo o propósito da migração do Alembic para a tabela event_log
"""cria tabela event_log

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-03

"""

# Importa o tipo Sequence e Union da biblioteca padrão para anotações de tipagem do Alembic
from typing import Sequence, Union

# Importa a biblioteca sqlalchemy para definição de tipos de colunas e esquemas de banco
import sqlalchemy as sa
# Importa a biblioteca op do Alembic para execução de operações DDL de migração
from alembic import op
# Importa a extensão de tipos de dialeto nativos do PostgreSQL para suporte ao JSONB
from sqlalchemy.dialects.postgresql import JSONB

# Identificador único desta revisão de migração
revision: str = "0007"
# Identificador da migração anterior da qual esta revisão depende
down_revision: Union[str, None] = "0006"
# Rótulos de ramificação da migração
branch_labels: Union[str, Sequence[str], None] = None
# Migrações das quais esta revisão depende diretamente
depends_on: Union[str, Sequence[str], None] = None


# Função de aplicação da migração (upgrade) para criação da tabela no banco de dados
def upgrade() -> None:
    # Docstring descrevendo a função upgrade
    """Cria tabela event_log para eventos de streaming."""
    # Chama op.create_table do Alembic para criar a nova tabela event_log no PostgreSQL
    op.create_table(
        # Define o nome da tabela a ser criada no banco
        "event_log",
        # Coluna event_id do tipo Text como chave primária única do evento
        sa.Column("event_id", sa.Text(), primary_key=True),
        # Coluna event_type do tipo Text para categorização do tipo do evento (obrigatoriedade não nula)
        sa.Column("event_type", sa.Text(), nullable=False),
        # Coluna user_id do tipo BigInteger opcional (nula quando for evento anônimo)
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        # Coluna movie_id do tipo BigInteger opcional
        sa.Column("movie_id", sa.BigInteger(), nullable=True),
        # Coluna payload do tipo JSONB do PostgreSQL para armazenamento de dados semiestruturados
        sa.Column("payload", JSONB(), nullable=True),
        # Coluna event_timestamp com fuso horário informando a data/hora original do evento (não nula)
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        # Coluna ingestion_timestamp com fuso horário informando o momento da gravação com default NOW()
        sa.Column("ingestion_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


# Função de reversão da migração (downgrade) para desazer as alterações no banco
def downgrade() -> None:
    # Docstring descrevendo a função downgrade
    """Remove a tabela event_log."""
    # Executa a instrução DDL DROP TABLE para remover a tabela event_log do PostgreSQL
    op.drop_table("event_log")
