"""${message}

Identificador da Revisão (ID da Migração): ${up_revision}
Revisão Anterior (de onde partiu): ${down_revision | comma,n}
Data de Criação: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Identificadores de revisão usados pelo Alembic para rastrear a ordem das migrações
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Função executada quando aplicamos a migração (sobe a versão do banco).
    
    Aqui você deve colocar os comandos para criar tabelas, colunas, chaves primárias, etc.
    Exemplo: op.create_table(...)
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Função executada quando revertemos a migração (desce a versão do banco).
    
    Aqui você deve colocar o código inverso da função upgrade() para desfazer as alterações.
    Exemplo: op.drop_table(...)
    """
    ${downgrades if downgrades else "pass"}