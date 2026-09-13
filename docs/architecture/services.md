# Serviços Docker — CineLake AI

Abaixo estão listados todos os containers e serviços orquestrados via `docker-compose.yml`:

| Serviço    | Descrição                                   | Porta          |
|------------|---------------------------------------------|----------------|
| PostgreSQL | Banco de dados principal (com pgvector)     | 127.0.0.1:5432 |
| MinIO      | Armazenamento de objetos (Data Lake S3)     | 127.0.0.1:9000 |
| Airflow    | Orquestração de pipelines e DAGs            | 127.0.0.1:8080 |
| MLflow     | Tracking server e Model Registry            | 127.0.0.1:5000 |
| Redis      | Cache e armazenamento em memória            | 127.0.0.1:6379 |
| Kafka      | Streaming e mensageria distribuída          | 127.0.0.1:9092 |
| ZooKeeper  | Coordenação do cluster Kafka                | 127.0.0.1:2181 |
| Prometheus | Coleta e armazenamento de métricas TSDB     | 127.0.0.1:9090 |
| Grafana    | Dashboards de observabilidade e alertas     | 127.0.0.1:3000 |
| API        | Aplicação principal FastAPI                 | 127.0.0.1:8002 |
| MCP        | Servidor MCP remoto para agentes de IA      | 127.0.0.1:8010 |
| Nginx      | Proxy reverso, rate limiting e TLS/HTTPS    | 0.0.0.0:80/443 |
