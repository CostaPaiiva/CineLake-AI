# Benchmarks — CineLake AI

Este diretório contém os resultados dos benchmarks executados no projeto.

## Metodologia

- Cada benchmark é executado com **3 a 5 repetições**.
- O primeiro resultado é descartado em benchmarks com cache.
- Os tempos reportados são médias.
- Ambiente: VPS Ubuntu, CPU compartilhada, disco SSD.

## Benchmarks disponíveis

- `csv_vs_parquet`: leitura de CSV vs Parquet.
- `index_vs_no_index`: consulta SQL com e sem índice.
- `redis_vs_no_redis`: acesso com e sem cache.
- `incremental_vs_full`: ingestão completa vs incremental.
- `partition_pruning`: leitura completa vs com pruning.

## Como executar

```bash
python -m cinelake run-benchmarks
```

Os resultados são salvos em `docs/benchmarks/resultados.json` e registrados no MLflow.
