"""cria tabela rag_query_log

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-31

"""  # Docstring informando o objetivo da migração e metadados de revisão do Alembic.

from collections.abc import Sequence  # Importa Sequence para tipagem compatível com coleções Python.
from typing import Union  # Importa Union para declarações de tipos opcionais.

from alembic import op  # Importa o módulo de operações DDL do framework Alembic.
import sqlalchemy as sa  # Importa a biblioteca SQLAlchemy para definição de tipos de colunas e constraints.
from sqlalchemy.dialects.postgresql import JSONB  # Importa o tipo de dados nativo JSONB do dialeto PostgreSQL.


# revision identifiers, used by Alembic.
revision: str = "0005"  # Identificador único desta revisão da migração.
down_revision: Union[str, None] = "0004"  # Identificador da revisão anterior na árvore de versões do Alembic.
branch_labels: Union[str, Sequence[str], None] = None  # Rótulos de ramificação (branch labels) opcionais.
depends_on: Union[str, Sequence[str], None] = None  # Dependências adicionais de migração opcionais.


def upgrade() -> None:  # Define a função de avanço (upgrade) da migração de schema.
    """Cria a tabela de auditoria para consultas RAG."""  # Docstring descrevendo a ação da função upgrade.
    op.create_table(  # Executa a operação DDL de criação da nova tabela no banco de dados.
        "rag_query_log",  # Nome da tabela de log e auditoria de consultas do RAG.
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),  # Coluna de chave primária inteira autoincrementável (BigInteger).
        sa.Column("pergunta", sa.Text(), nullable=False),  # Coluna de texto contendo a pergunta submetida pelo usuário.
        sa.Column("documentos_recuperados", JSONB(), nullable=True),  # Coluna JSONB armazenando os documentos retornados na busca vetorial.
        sa.Column("ferramenta_mcp", sa.Text(), nullable=True),  # Coluna textual armazenando o nome da ferramenta MCP acionada (se houver).
        sa.Column("resultado_ferramenta", JSONB(), nullable=True),  # Coluna JSONB contendo a resposta retornada pela ferramenta MCP.
        sa.Column("latencia_ms", sa.Float(), nullable=True),  # Coluna numérica em ponto flutuante registrando o tempo de resposta em milissegundos.
        sa.Column("status_code", sa.Integer(), nullable=True),  # Coluna inteira registrando o código de status HTTP da requisição.
        sa.Column("erro", sa.Text(), nullable=True),  # Coluna de texto contendo a mensagem ou rastreio de erro em caso de falha.
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),  # Coluna temporal com fuso horário registrando o momento do log.
    )  # Fecha a definição da tabela rag_query_log.


def downgrade() -> None:  # Define a função de reversão (downgrade) da migração de schema.
    """Remove a tabela rag_query_log."""  # Docstring descrevendo a ação da função downgrade.
    op.drop_table("rag_query_log")  # Executa a operação DDL de exclusão da tabela rag_query_log caso seja feito rollback.
