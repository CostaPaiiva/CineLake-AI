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

---

## 9 — Execução

### 1. Obter chave da API TMDB

Acesse [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) (crie conta gratuita se necessário) e gere uma chave.

### 2. Adicionar chave ao `.env`

Na VPS, edite o arquivo `.env`:

```bash
nano .env
```