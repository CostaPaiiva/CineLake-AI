# 📖 Guia Operacional — CineLake AI

Este documento reúne os comandos essenciais para operação, manutenção e desenvolvimento da plataforma, tanto localmente quanto na VPS.

---

## 🔒 1. Segurança e Boas Práticas

- **Nunca comite arquivos `.env` ou chaves de API / chaves SSH no GitHub.**
- O arquivo `.gitignore` está configurado para ignorar automaticamente:
  - Arquivos de ambiente (`.env`, `.env.*`)
  - Chaves e certificados (`*.pem`, `*.key`, `*.id_rsa`)
  - Arquivos de dados locais (`data/`, `*.parquet`, `*.csv`)
  - Artefatos e logs de compilação do dbt (`target/`, `logs/`, `dbt_packages/`)

---

## 🌐 2. Acesso à VPS e Túneis SSH

Para conectar à VPS mantendo a conexão ativa (anti-timeout de 60 segundos) e criando os túneis de portas para os serviços:

### Túnel para Airflow / Aplicações Web (Porta 8080)
```bash
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L 8080:127.0.0.1:8080 <SEU_USUARIO>@<IP_DA_VPS>
```
*Acesso local no navegador: `http://localhost:8080`*

### Túnel para o Console do MinIO Data Lake (Porta 9001)
```bash
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L 9001:127.0.0.1:9001 <SEU_USUARIO>@<IP_DA_VPS>
```
*Acesso local no navegador: `http://localhost:9001`*

---

## 🐳 3. Infraestrutura Docker

Gerenciamento dos serviços conteinerizados (PostgreSQL, MinIO, etc.):

```bash
# Subir todos os serviços em background
docker compose up -d

# Visualizar status dos containers
docker compose ps

# Visualizar logs em tempo real
docker compose logs -f

# Parar os serviços
docker compose down
```

---

## 🗄️ 4. Banco de Dados e Migrações (Alembic)

```bash
# Aplicar todas as migrações pendentes
alembic upgrade head

# Reverter a última migração
alembic downgrade -1

# Criar uma nova migração
alembic revision -m "nome_da_migracao"
```

---

## 🔄 5. Pipelines de Ingestão de Dados

```bash
# Ingestão de filmes do TMDb (Requer TMDB_API_KEY no .env)
python -m cinelake ingest-tmdb --output-dir data/raw/tmdb

# Ingestão de teste com limite de filmes
python -m cinelake ingest-tmdb --output-dir data/raw/tmdb --max-filmes 10

# Ingestão para a Camada Bronze do Data Lake (MinIO + Parquet)
python -m cinelake ingest-datalake-bronze
```

---

## 🏗️ 6. Transformação e Modelagem Dimensional (dbt)

```bash
# Navegar até o diretório do dbt
cd dbt_project

# Testar conexão com o banco PostgreSQL
dbt debug

# Executar todas as transformações (Staging e Marts)
dbt run

# Executar apenas modelos de Staging
dbt run --select staging

# Executar apenas modelos da Camada Marts (Star Schema)
dbt run --select marts

# Executar todos os testes de qualidade de dados (not_null, unique, relationships)
dbt test

# Gerar e visualizar a documentação interativa do dbt
dbt docs generate
dbt docs serve
```

---

## 🧪 7. Qualidade de Código e Testes

```bash
# Executar a suíte de testes unitários
pytest

# Executar testes com relatório de cobertura
pytest --cov=src/cinelake

# Linter e formatação com Ruff
ruff check .
ruff format .
```