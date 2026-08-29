"""Métricas do pipeline expostas via Prometheus."""

import time

from prometheus_client import Counter, Gauge, Histogram

# Métricas
# Contador total de execuções do pipeline categorizadas por nome e status (ex: success, error)
PIPELINE_RUNS_TOTAL = Counter(
    "cinelake_pipeline_runs_total",
    "Total de execuções de pipeline por status",
    ["pipeline", "status"],
)

# Histograma para medir a distribuição do tempo de execução dos pipelines em segundos
PIPELINE_DURATION_SECONDS = Histogram(
    "cinelake_pipeline_duration_seconds",
    "Duração das execuções de pipeline",
    ["pipeline"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

# Indicador (Gauge) da quantidade exata de linhas/registros processados na última execução
PIPELINE_ROWS_PROCESSED = Gauge(
    "cinelake_pipeline_rows_processed",
    "Quantidade de linhas processadas na última execução",
    ["pipeline"],
)

# Indicador (Gauge) com o timestamp Unix da última execução concluída com sucesso
PIPELINE_LAST_SUCCESS_TIMESTAMP = Gauge(
    "cinelake_pipeline_last_success_timestamp",
    "Timestamp da última execução bem-sucedida",
    ["pipeline"],
)


def registrar_execucao_pipeline(pipeline: str, status: str, duracao: float, linhas: int) -> None:
    """Registra as métricas observáveis de uma execução completa de pipeline no Prometheus.

    Args:
        pipeline: Nome identificador do pipeline (ex: 'ingestao_tmdb').
        status: Status final da execução (ex: 'success', 'error').
        duracao: Tempo total de execução em segundos.
        linhas: Quantidade de registros/linhas processadas na execução.
    """
    # Incrementa o contador de execuções para o pipeline e status informados
    PIPELINE_RUNS_TOTAL.labels(pipeline=pipeline, status=status).inc()

    # Registra a duração no histograma de métricas
    PIPELINE_DURATION_SECONDS.labels(pipeline=pipeline).observe(duracao)

    # Atualiza a quantidade de linhas processadas na última execução
    PIPELINE_ROWS_PROCESSED.labels(pipeline=pipeline).set(linhas)

    # Se o status for de sucesso, atualiza o timestamp da última execução bem-sucedida
    if status == "success":
        PIPELINE_LAST_SUCCESS_TIMESTAMP.labels(pipeline=pipeline).set(time.time())
