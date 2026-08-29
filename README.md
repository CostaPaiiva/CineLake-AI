# CineLake AI

Plataforma de Engenharia de Dados, Recomendação e IA Agêntica de nível produção.

## Status

**FASE 3 — MOVIELENS**

## O que é o CineLake AI?

O CineLake AI é uma plataforma completa de dados que utiliza dados reais de filmes para demonstrar:

- Engenharia de Dados
- Arquitetura de Dados
- Processamento Batch
- Streaming
- Data Lake
- Data Warehouse
- Modelagem Dimensional
- Qualidade de Dados
- Contratos de Dados
- Linhagem de Dados
- Orquestração
- Observabilidade
- Machine Learning
- Sistemas de Recomendação
- MLOps
- APIs
- Geração Aumentada por Recuperação (RAG)
- Model Context Protocol (MCP)
- CI/CD

## Ambiente de desenvolvimento

A plataforma roda em uma única VPS Ubuntu.  
O PC local é usado apenas para PowerShell SSH, navegador e Power BI.

## Estrutura atual do repositório

```text
cinelake-ai/
├── src/
│   └── cinelake/
│       ├── datalake/
│       │   ├── bronze_ingest.py
│       │   └── minio_client.py
│       ├── ingestion/
│       │   ├── movielens/
│       │   └── tmdb/
│       ├── config.py
│       ├── db.py
│       └── __main__.py
├── alembic/
├── tests/
│   └── unit/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Ingestão TMDB

Obtenha uma chave de API gratuita em [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) e adicione ao `.env`:

```bash
TMDB_API_KEY=sua_chave
```

Execute a ingestão incremental:

```bash
python -m cinelake ingest-tmdb --output-dir data/raw/tmdb
```

Para testar com poucos filmes:

```bash
python -m cinelake ingest-tmdb --output-dir data/raw/tmdb --max-filmes 10
```

---

## Data Lake (MinIO + Parquet)

Subir o MinIO:

```bash
docker compose up -d minio
```
Acessar console web: http://<IP_DA_VPS>:9001 (somente via túnel SSH ou localmente).

Popular a camada bronze:

```bash
python -m cinelake ingest-datalake-bronze
```
Os arquivos Parquet ficam no bucket data-lake sob bronze/.

---

## 8 — Explicação

### `TMDBClient`

- **Rate limiting**: `_respeitar_rate_limit()` garante intervalo mínimo entre chamadas.
- **Retry com backoff exponencial**: tenta até 5 vezes, dobrando o tempo de espera.
- **Timeout**: 10 segundos por requisição.
- **Erro 404**: retorna dicionário vazio (filme não encontrado no TMDB), sem retentar.
- **Logging**: registra cada tentativa, erros e sucesso.

### `ingerir_tmdb`

- **Watermark incremental**: lê `last_processed_movie_id` da tabela `tmdb_ingestion_state` e busca apenas `movie_id > watermark`.
- **Atualiza watermark** a cada filme processado com sucesso.
- **Salva JSONs brutos** em `data/raw/tmdb/<movie_id>_<tipo>.json`.
- **Registra batch** em `ingestion_batch` para auditoria.
- **Interrompe em erro**: se um filme falhar, levanta exceção para não pular silenciosamente.

### Configuração

- `TMDB_API_KEY` adicionada ao `.env.example` e `Settings`.
- Chave é obrigatória; sem ela, a ingestão falhará.

### Migração

- Nova tabela `tmdb_ingestion_state` com uma única linha (id=1) para armazenar o watermark.

### MinIO

- Adicionado ao `docker-compose.yml` como serviço separado.
- Exposto apenas em `127.0.0.1:9000` (API) e `127.0.0.1:9001` (console web), sem acesso externo direto.
- Usa volume nomeado `minio_data` para persistência.
- Healthcheck com `curl` para verificar se está vivo.

### Cliente MinIO

- Usa `boto3` com endpoint do MinIO e credenciais do `.env`.
- `garantir_bucket()` cria o bucket se não existir.
- `fazer_upload_parquet()` faz upload de arquivos locais para o bucket.

### Ingestão Bronze

- Converte CSVs do MovieLens para Parquet usando pandas/pyarrow.
- Converte JSONs do TMDB (um arquivo por tipo) para Parquet.
- Envia os arquivos para `bronze/` no MinIO.
- Registra cada execução na tabela `ingestion_batch` com fonte `datalake_bronze`.

### Separação de responsabilidades

- `minio_client.py` lida com conexão e upload.
- `bronze_ingest.py` orquestra a conversão e envio.

---

## Qualidade de Dados (Great Expectations)

Configurar GE:

```bash
python -c "from cinelake.data_quality.setup import configurar_ge; from cinelake.data_quality.validate import criar_data_context; ctx=criar_data_context(); configurar_ge(ctx)"
```

Validar ratings:

```bash
python -c "from cinelake.data_quality.validate import validar_ratings; print(validar_ratings())"
```

Os resultados HTML ficam em `great_expectations/uncommitted/data_docs/local_site/validations/`.

---

## 8 — Explicação

### Great Expectations

- **Data Context**: configuração central do GE, geralmente criada em `great_expectations/`.
- **Datasource**: conexão com a fonte de dados (PostgreSQL).
- **Expectation Suite**: coleção de expectativas.
- **Checkpoint**: executa a validação e gera resultados.

### Contrato de dados

- `RATINGS_CONTRACT` define colunas, tipos e restrições.
- É usado para construir a suíte de expectativas programaticamente.

### Validação

- `validar_ratings()` cria um batch request para a tabela `ratings` e executa o checkpoint.
- Retorna resumo com sucesso/fracasso.

### Integração com Airflow

- DAG `run_data_quality` chama a validação e falha se a qualidade não passar.

---

## 9 — Execução

### 1. Obter chave da API TMDB

Acesse [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) (crie conta gratuita se necessário) e gere uma chave.

### 2. Adicionar chave ao `.env`

Na VPS, edite o arquivo `.env` e adicione sua chave `TMDB_API_KEY`.

### 3. Atualizar dependências

Na VPS, com ambiente virtual ativo:

```bash
pip install -e ".[dev]"
```

### 4. Subir o MinIO

```bash
docker compose up -d minio
```

Verifique o status do container:

```bash
docker compose ps
```

### 5. Acessar console web (opcional)

No seu PC, se quiser acessar o console web do MinIO, crie um túnel SSH:

No PC (PowerShell):

```powershell
ssh -L 9001:127.0.0.1:9001 <SEU_USUARIO>@<IP_DA_VPS>
```

Depois abra no navegador: http://127.0.0.1:9001.
Use as credenciais do `.env` (`MINIO_ACCESS_KEY` e `MINIO_SECRET_KEY`).

### 6. Popular camada bronze

Na VPS, execute:

```bash
python -m cinelake ingest-datalake-bronze
```

### 7. Verificar arquivos no MinIO

Via console web ou usando aws CLI (se instalado) com endpoint apontando para o MinIO.
Ou, opcionalmente, use a biblioteca `boto3` no Python para listar objetos:

```bash
python -c "
from cinelake.datalake.minio_client import criar_cliente_minio
from cinelake.config import settings
cliente = criar_cliente_minio()
resposta = cliente.list_objects_v2(Bucket=settings.minio_bucket, Prefix='bronze/')
for obj in resposta.get('Contents', []):
    print(obj['Key'])
"
```

---

## Observabilidade Básica

Subir API de observabilidade:

```bash
python -m cinelake serve-observability --host 127.0.0.1 --port 8000
```

Endpoints disponíveis:

- `GET /health` – status geral da plataforma.
- `GET /metrics` – contagens e freshness das fontes.
- `GET /freshness` – freshness por fonte.

Exemplo:

```bash
curl http://127.0.0.1:8000/health
```

---

## 8 — Explicação

### `health.py`

- `verificar_conexao_postgres()`: faz `SELECT 1` para validar conexão.
- `obter_contagens_tabelas()`: conta linhas das tabelas principais, incluindo tabelas marts do dbt.
- `obter_ultimas_execucoes()`: consulta `ingestion_batch` para pegar última execução bem-sucedida por fonte e calcula freshness.
- `coletar_status_geral()`: agrega tudo.

### `api.py`

- Define endpoints FastAPI que chamam as funções de coleta.
- Tratamento de erros com HTTP 500.

### Comando CLI

- `serve-observability` inicia o servidor Uvicorn para expor a API.

---

## 9 — Execução

### 1. Instalar dependências

```bash
pip install -e ".[dev]"
```