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
│       │   └── movielens/
│       ├── config.py
│       ├── db.py
│       └── __main__.py
├── alembic/
├── tests/
│   └── unit/
├── docker-compose.yml
├── pyproject.toml
└── README.md