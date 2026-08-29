# ==============================================================================
# validate.py - Módulo de Validação de Dados com Great Expectations
# ==============================================================================
"""Funções para validar dados com Great Expectations."""

import logging

from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.data_context import BaseDataContext
from great_expectations.data_context.types.base import (
    DataContextConfig,
    FilesystemStoreBackendDefaults,
)

from typing import Any

# Configuração do logger do módulo
logger = logging.getLogger(__name__)


def criar_data_context() -> BaseDataContext:
    """
    Cria ou carrega o Data Context do Great Expectations na raiz do projeto.

    Returns:
        BaseDataContext: Instância do contexto do Great Expectations.
    """
    data_context_config = DataContextConfig(
        store_backend_defaults=FilesystemStoreBackendDefaults(root_directory="great_expectations"),
    )
    contexto = BaseDataContext(project_config=data_context_config)
    return contexto


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
