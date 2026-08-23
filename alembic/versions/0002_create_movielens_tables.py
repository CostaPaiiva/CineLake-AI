"""cria tabelas do MovieLens

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de revisão do Alembic para controle de versão do banco de dados
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as tabelas movies, ratings, tags, links e ingestion_batch."""
    
    # Cria a tabela de filmes (movies) contendo ID, título e gêneros do MovieLens
    op.create_table(
        "movies",
        sa.Column("movie_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("genres", sa.Text(), nullable=False),
    )

    # Cria a tabela de avaliações (ratings) com chaves primárias compostas (user_id, movie_id, ts)
    op.create_table(
        "ratings",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("movie_id", sa.BigInteger(), primary_key=True),
        sa.Column("rating", sa.Numeric(2, 1), nullable=False),
        sa.Column("ts", sa.BigInteger(), primary_key=True),
    )

    # Cria a tabela de tags aplicadas pelos usuários aos filmes, com chave primária composta
    op.create_table(
        "tags",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("movie_id", sa.BigInteger(), primary_key=True),
        sa.Column("tag", sa.Text(), primary_key=True),
        sa.Column("ts", sa.BigInteger(), primary_key=True),
    )

    # Cria a tabela de links externos ligando o ID do MovieLens aos IDs do IMDb e TMDb
    op.create_table(
        "links",
        sa.Column("movie_id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("imdb_id", sa.BigInteger(), nullable=True),
        sa.Column("tmdb_id", sa.BigInteger(), nullable=True),
    )

    # Cria a tabela de logs e controle de ingestão (ingestion_batch)
    op.create_table(
        "ingestion_batch",
        sa.Column("batch_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.Text(), nullable=False),            # Origem dos dados ingestados
        sa.Column("status", sa.Text(), nullable=False),            # Status do lote (ex: success, error, running)
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),   # Data/hora de início
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),  # Data/hora de conclusão
        sa.Column("rows_processed", sa.BigInteger(), nullable=False, server_default="0"), # Total processado
        sa.Column("rows_inserted", sa.BigInteger(), nullable=False, server_default="0"),  # Linhas inseridas
        sa.Column("rows_updated", sa.BigInteger(), nullable=False, server_default="0"),   # Linhas atualizadas
        sa.Column("error_message", sa.Text(), nullable=True),      # Mensagem de erro caso ocorra falha
    )


def downgrade() -> None:
    """Remove as tabelas do MovieLens e de controle."""
    # Exclusão das tabelas na ordem reversa de dependência/criação
    op.drop_table("ingestion_batch")
    op.drop_table("links")
    op.drop_table("tags")
    op.drop_table("ratings")
    op.drop_table("movies")