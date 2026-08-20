# CineLake AI

Production-Grade Data Engineering, Recommendation & Agentic Data Platform

## Status

**FASE 1 — Foundation**

## What is CineLake AI?

CineLake AI is a full data platform that uses real movie data to demonstrate:

- Data Engineering
- Data Architecture
- Batch Processing
- Streaming
- Data Lake
- Data Warehouse
- Dimensional Modeling
- Data Quality
- Data Contracts
- Data Lineage
- Orchestration
- Observability
- Machine Learning
- Recommendation Systems
- MLOps
- APIs
- Retrieval-Augmented Generation (RAG)
- Model Context Protocol (MCP)
- CI/CD

## Development environment

The platform runs on a single VPS Ubuntu using VS Code Remote SSH.

Local PC is used only for:

- VS Code
- SSH
- Browser
- Power BI Desktop later

## Current repository layout

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
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md