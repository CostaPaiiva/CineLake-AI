# Docstring do módulo descrevendo a avaliação unificada de todos os modelos de recomendação
"""Avaliação unificada dos modelos de recomendação."""

# Importa o módulo nativo de logging do Python para registro de métricas e status de execução
import logging

# Importa os tipos Any e Dict para anotação de tipos
from typing import Any

# Importa as funções de avaliação do módulo evaluate
from cinelake.recommender.evaluate import (
    avaliar_modelo,
    avaliar_modelo_popularidade,
)

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)


# Define a função principal de avaliação unificada dos modelos de recomendação
def avaliar_modelos(top_k: int = 10) -> dict[str, dict[str, Any]]:
    # Docstring da função descrevendo a comparação entre popularidade, content-based, colaborativo e híbrido
    """Avalia todos os modelos de recomendação (popularidade, content-based, colaborativo, híbrido)."""
    # Dicionário para armazenar as métricas finais de cada modelo avaliado
    resultados: dict[str, dict[str, Any]] = {}

    # Executa e armazena as métricas do modelo de popularidade baseline
    resultados["popularity_baseline"] = avaliar_modelo_popularidade(top_k)

    # Percorre e avalia os modelos que possuem recomendações salvas no banco de dados
    for model_name in ["content_based", "collaborative_item_item", "hybrid"]:
        # Avalia o modelo específico para top_k recomendações
        res = avaliar_modelo(model_name, top_k=top_k)
        # Armazena o resultado no dicionário de métricas
        resultados[model_name] = res

    # Retorna o dicionário completo contendo os resultados de todos os modelos
    return resultados
