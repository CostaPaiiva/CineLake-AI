# Dockerfile
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de projeto
COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY dbt_project ./dbt_project

# Instala dependências
RUN pip install --upgrade pip && pip install -e ".[dev]"

# Usuário não-root
RUN useradd -m cinelake && chown -R cinelake:cinelake /app
USER cinelake

EXPOSE 8002

CMD ["python", "-m", "cinelake", "serve-main-api", "--host", "0.0.0.0", "--port", "8002"]
