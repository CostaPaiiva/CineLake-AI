# CineLake AI

Plataforma de Engenharia de Dados, Recomendação e Agentes de Dados de Nível de Produção

## Status

**FASE 2 — Docker + PostgreSQL**

## O que é o CineLake AI?

O CineLake AI é uma plataforma de dados completa que utiliza dados reais de filmes para demonstrar:

- Engenharia de Dados
- Arquitetura de Dados
- Processamento em Batch
- Processamento em Streaming
- Data Lake
- Data Warehouse
- Modelagem Dimensional
- Qualidade de Dados (Data Quality)
- Contratos de Dados (Data Contracts)
- Linhagem de Dados (Data Lineage)
- Orquestração
- Observabilidade
- Machine Learning
- Sistemas de Recomendação
- MLOps
- APIs
- Geração Aumentada de Recuperação (RAG)
- Model Context Protocol (MCP)
- CI/CD

## Ambiente de Desenvolvimento

A plataforma roda em uma única VPS Ubuntu.  
O computador local é utilizado para SSH via PowerShell, navegador e, posteriormente, Power BI.

## Estrutura Atual do Repositório

```text
cinelake-ai/
├── .github/
│   └── workflows/
├── src/
│   └── cinelake/
├── ingestion/
├── airflow/
├── dbt_project/
├── streaming/
├── recommender/
├── api/
├── rag/
├── mcp_server/
├── data_quality/
├── monitoring/
├── infrastructure/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── runbooks/
│   ├── data-model/
│   ├── rag/
│   ├── mcp/
│   └── benchmarks/
├── powerbi/
├── scripts/
├── alembic/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```