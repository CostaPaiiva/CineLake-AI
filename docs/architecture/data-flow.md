# Fluxo de Dados — CineLake AI

O fluxo de dados da plataforma CineLake AI segue o ciclo de vida completo de dados desde a ingestão bruta até o consumo analítico e inteligência artificial.

## Ingestão

- **MovieLens**: CSV → PostgreSQL (camada bronze / dados históricos)
- **TMDB API**: API REST → JSON → PostgreSQL (camada bronze / metadados enriquecidos)
- **Eventos em Tempo Real**: Aplicação → Kafka (`movie-events`) → Consumer com validação → PostgreSQL / DLQ

## Transformação (dbt)

- **dbt Staging**: Views padronizadas com limpeza, casting de tipos e renomeação de colunas.
- **dbt Marts**: Tabelas analíticas modeladas em Star Schema (dimensional).
- **Modelos Dimensionais**:
  - `dim_movie`: Metadados consolidados dos filmes.
  - `dim_user`: Usuários e perfis analíticos.
  - `dim_date`: Dimensão de calendário e datas.
  - `fact_rating`: Fato transacional de avaliações.

## Consumo e Aplicações

- **Power BI / Dashboards**: Relatórios de BI conectados diretamente aos Data Marts.
- **Modelos de Recomendação**: Algoritmos Popularidade, Content-Based, Colaborativo e Híbrido.
- **API Principal (FastAPI)**: Endpoints REST para consulta de filmes, métricas e recomendações.
- **RAG + MCP**: Assistente inteligente de IA que auxilia o engenheiro de dados através de busca semântica no `pgvector` e ferramentas operacionais do MCP.

## Observabilidade e Auditoria

- `ingestion_batch`: Tabela de auditoria de lotes de ingestão e pipelines.
- `rag_query_log`: Tabela de auditoria de consultas, latência e respostas do assistente RAG.
- `mcp_audit_log`: Tabela de auditoria das ferramentas MCP executadas e seus resultados.
