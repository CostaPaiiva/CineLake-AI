"""Configuração do ambiente do Alembic.

Este arquivo é executado toda vez que chamamos comandos do Alembic (como `alembic upgrade`).
Ele define como o Alembic se conecta ao banco de dados e como lê os modelos do SQLAlchemy.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Importa as configurações do projeto para obter as variáveis de ambiente (como a URL do banco)
from cinelake.config import settings

# Objeto de configuração do Alembic, que dá acesso ao arquivo alembic.ini
config = context.config

# Interpreta o arquivo de configuração para configurar o sistema de logs do Python
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Configura dinamicamente a URL do banco de dados SQLAlchemy usando as configurações do seu projeto (.env)
# Isso substitui o valor 'sqlalchemy.url' definido de forma fixa no alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Defina aqui o objeto MetaData do seu modelo para suporte à geração automática ('autogenerate')
# Exemplo: de cinelake.db import Base; target_metadata = Base.metadata
target_metadata = None


def run_migrations_offline() -> None:
    """Executa as migrações no modo 'offline'.

    Este modo configura o contexto apenas com a URL do banco. Ele não abre uma conexão
    real com o banco de dados. Em vez disso, ele apenas gera os comandos SQL correspondentes
    e os exibe no terminal ou os salva em um arquivo (útil para quando você não tem acesso
    direto ao banco de produção).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # Inicia uma transação e roda as migrações
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa as migrações no modo 'online'.

    Este é o modo padrão. Ele cria uma engine de conexão do SQLAlchemy, conecta de fato
    ao banco de dados e executa as migrações diretamente nele.
    """
    # Cria a engine de conexão do SQLAlchemy a partir da URL configurada
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url") or "",
        poolclass=pool.NullPool,
    )

    # Abre a conexão com o banco de dados
    with connectable.connect() as connection:
        # Configura o contexto do Alembic com a conexão ativa
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        # Inicia uma transação no banco e executa as migrações
        with context.begin_transaction():
            context.run_migrations()


# Decisão de fluxo: se for modo offline, roda a função offline. Caso contrário, roda a online.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
