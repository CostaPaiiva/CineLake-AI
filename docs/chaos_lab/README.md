# Chaos Lab — CineLake AI

Este diretório documenta os cenários de injeção de falhas controladas.

## Cenários

- `postgres_down`: derruba o PostgreSQL por 20s.
- `minio_down`: derruba o MinIO por 20s.
- `kafka_down`: derruba o Kafka por 20s.
- `mcp_down`: mata o processo do MCP Server.
- `pipeline_failure`: insere um registro de falha em ingestion_batch.
- `dlq_event`: envia evento inválido para a DLQ.
- `high_latency`: simula latência alta.

## Como executar

```bash
# Executa um cenário individual
python -m cinelake chaos-lab --cenario postgres_down

# Executa todos os cenários em sequência
python -m cinelake chaos-lab --cenario all
```

Os resultados de execução são salvos estruturados em `docs/chaos_lab/resultados.json`.
