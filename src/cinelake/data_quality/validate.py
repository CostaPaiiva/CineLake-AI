# ==============================================================================
# validate.py - Módulo de Validação de Dados com Great Expectations
# ==============================================================================
"""Funções para validar dados com Great Expectations."""

import logging
from typing import Any

import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

# Configuração do logger do módulo
logger = logging.getLogger(__name__)


def criar_data_context() -> Any:
    """
    Cria ou carrega o Data Context do Great Expectations na raiz do projeto.

    Returns:
        Any: Instância do contexto do Great Expectations.
    """
    return ge.get_context(project_root_dir="great_expectations")


def validar_ratings() -> dict[str, Any]:
    """
    Executa a validação do Great Expectations na tabela ratings do PostgreSQL.

    Retorna:
        dict[str, Any]: Dicionário contendo o status de sucesso e os detalhes/estatísticas do checkpoint.
    """
    contexto = criar_data_context()

    # Define o batch request em tempo de execução para consultar a tabela de ratings no PostgreSQL
    batch_request = RuntimeBatchRequest(
        datasource_name="postgres_ratings",
        data_connector_name="default_runtime_data_connector_name",
        data_asset_name="ratings",
        runtime_parameters={
            "query": "SELECT * FROM ratings LIMIT 1000",
        },
        batch_identifiers={"default_identifier_name": "ratings_batch"},
    )

    # Configura o checkpoint para execução da suíte de expectativas de qualidade de dados
    checkpoint_config = {
        "name": "ratings_checkpoint",
        "config_version": 1,
        "class_name": "SimpleCheckpoint",
        "validations": [
            {
                "batch_request": batch_request.to_dict(),
                "expectation_suite_name": "ratings_suite",
            }
        ],
    }
    if hasattr(contexto, "add_or_update_checkpoint"):
        contexto.add_or_update_checkpoint(**checkpoint_config)
    elif hasattr(contexto, "checkpoints") and hasattr(contexto.checkpoints, "add_or_update"):
        from great_expectations.checkpoint import SimpleCheckpoint
        cp = SimpleCheckpoint(name="ratings_checkpoint", data_context=contexto, **checkpoint_config)
        contexto.checkpoints.add_or_update(cp)
    else:
        contexto.add_checkpoint(**checkpoint_config)

    # Executa o checkpoint e obtém os resultados da suíte
    resultados = contexto.run_checkpoint(checkpoint_name="ratings_checkpoint")

    # Extrai o resumo da execução
    resumo = {
        "success": resultados["success"],
        "statistics": resultados["run_results"],
    }
    logger.info("Resultado da validação: %s", resumo["success"])
    return resumo
