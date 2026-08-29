"""Testes unitários para as métricas do Prometheus."""

from cinelake.observability.metrics import (
    PIPELINE_RUNS_TOTAL,
    registrar_execucao_pipeline,
)


def test_registrar_execucao_pipeline_incrementa_contador(monkeypatch) -> None:
    """Valida se o registro de execução de pipeline incrementa o contador PIPELINE_RUNS_TOTAL."""
    # Limpa as métricas antes de executar o teste para isolamento de estado
    PIPELINE_RUNS_TOTAL.clear()

    # Executa a função helper de registro de métrica
    registrar_execucao_pipeline("teste", "success", 1.0, 10)

    # Obtém o valor atualizado do contador para o rótulo especificado
    valor = PIPELINE_RUNS_TOTAL.labels(pipeline="teste", status="success")._value.get()

    # Valida se a contagem foi incrementada exatamente para 1.0
    assert valor == 1.0
