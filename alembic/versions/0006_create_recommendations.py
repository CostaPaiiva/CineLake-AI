# Docstring do módulo descrevendo o propósito da migração
"""cria tabela recommendations

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-01

"""
# Importa tipo Sequence do módulo collections.abc para compatibilidade com versões recentes do Python
from collections.abc import Sequence

# Importa a biblioteca sqlalchemy como sa para definição de tabelas e colunas
import sqlalchemy as sa

# Importa a biblioteca op do Alembic para execução de operações no banco de dados
from alembic import op

# Define o identificador único desta revisão de migração
revision: str = "0006"
# Define o identificador da migração anterior sobre a qual esta depende
down_revision: str | None = "0005"
# Define os rótulos de ramificação (branch labels), caso existam
branch_labels: Sequence[str] | str | None = None
# Define outras migrações de dependência, caso existam
depends_on: Sequence[str] | str | None = None


# Define a função de atualização da migração (aplicar mudanças no banco)
def upgrade() -> None:
    # Docstring explicativa da função upgrade
    """Cria tabela de recomendações."""
    # Chama o método de criação de tabela do Alembic
    op.create_table(
        # Especifica o nome da tabela a ser criada
        "recommendations",
        # Cria a coluna 'user_id' como BigInteger não nulo
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        # Cria a coluna 'movie_id' como BigInteger não nulo
        sa.Column("movie_id", sa.BigInteger(), nullable=False),
        # Cria a coluna 'score' como Float não nulo
        sa.Column("score", sa.Float(), nullable=False),
        # Cria a coluna 'rank' como Integer não nulo
        sa.Column("rank", sa.Integer(), nullable=False),
        # Cria a coluna 'model_name' como Text não nulo
        sa.Column("model_name", sa.Text(), nullable=False),
        # Cria a coluna 'created_at' como DateTime com fuso horário e valor default da data/hora atual no banco
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Configura a chave primária composta com as colunas user_id, movie_id e model_name
        sa.PrimaryKeyConstraint("user_id", "movie_id", "model_name"),
    )


# Define a função de reversão da migração (desfazer alterações)
def downgrade() -> None:
    # Docstring explicativa da função downgrade
    """Remove a tabela recommendations."""
    # Executa a remoção (drop) da tabela 'recommendations'
    op.drop_table("recommendations")
