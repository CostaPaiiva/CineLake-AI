# ==============================================================================
# setup.py - Configuração Inicial de Datasource e Suíte do Great Expectations
# ==============================================================================
"""Configuração inicial do Great Expectations."""

try:
    from great_expectations.data_context import AbstractDataContext as BaseDataContext
except ImportError:
    from great_expectations.data_context import BaseDataContext  # type: ignore[attr-defined]

from cinelake.config import settings


def configurar_ge(contexto: BaseDataContext) -> None:
    """
    Adiciona o datasource PostgreSQL ao contexto do Great Expectations
    e gera programaticamente a suíte ratings_suite a partir do contrato de dados.

    Args:
        contexto (BaseDataContext): Contexto ativo do Great Expectations.
    """
    # Configura o Datasource para conexão com o banco PostgreSQL via SqlAlchemyExecutionEngine
    datasource_config = {
        "name": "postgres_ratings",
        "class_name": "Datasource",
        "execution_engine": {
            "class_name": "SqlAlchemyExecutionEngine",
            "connection_string": settings.database_url,
        },
        "data_connectors": {
            "default_runtime_data_connector_name": {
                "class_name": "RuntimeDataConnector",
                "batch_identifiers": ["default_identifier_name"],
            }
        },
    }
    if hasattr(contexto, "sources") and hasattr(contexto.sources, "add_postgres"):
        try:
            contexto.sources.add_postgres(name="postgres_ratings", connection_string=settings.database_url)
        except Exception:
            pass
    elif hasattr(contexto, "add_or_update_datasource"):
        contexto.add_or_update_datasource(**datasource_config)
    else:
        contexto.add_datasource(**datasource_config)

    # Carrega a suíte de expectativas ou cria uma nova se estiver vazia
    suite = contexto.get_expectation_suite("ratings_suite")
    if not suite.expectations:
        from cinelake.data_quality.data_contracts.ratings_contract import RATINGS_CONTRACT

        # Itera sobre as restrições definidas no contrato de dados (RATINGS_CONTRACT)
        for constraint in RATINGS_CONTRACT["constraints"]:
            expectation_name = constraint["expectation"]
            kwargs = {k: v for k, v in constraint.items() if k != "expectation"}

            # Adiciona cada expectativa de validação à suíte
            suite.add_expectation(
                expectation_configuration={
                    "expectation_type": expectation_name,
                    "kwargs": kwargs,
                }
            )
        # Salva a suíte de expectativas no projeto do Great Expectations
        contexto.save_expectation_suite(suite, "ratings_suite")
