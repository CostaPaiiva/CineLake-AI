# Docstring do módulo indicando o modelo híbrido que combina abordagens baseadas em conteúdo, colaborativa e popularidade
"""Modelo híbrido que combina content-based e colaborativo."""

# Importa o módulo nativo de logging do Python para registro de diagnósticos e avisos
import logging

# Importa Any do módulo typing para anotações de tipo flexíveis (ex: modelo SVD)
from typing import Any

# Importa a biblioteca numpy para operações com vetores e normalização numérica
import numpy as np

# Importa a função de recomendação colaborativa do módulo collaborative
from cinelake.recommender.collaborative import recomendar_colaborativo

# Importa a função de recomendação baseada em conteúdo do módulo content_based
from cinelake.recommender.content_based import recomendar_content_based

# Importa a função de cálculo de popularidade global do módulo popularity
from cinelake.recommender.popularity import calcular_popularidade

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)


# Define a função de recomendação híbrida agregando as três estratégias de recomendação
def recomendar_hibrido(
    user_id: int,
    modelo_svd: Any,
    top_n: int = 10,
    peso_cb: float = 0.4,
    peso_cf: float = 0.4,
    peso_pop: float = 0.2,
) -> list[tuple[int, float]]:
    # Docstring da função detalhando os parâmetros e o cálculo ponderado dos scores
    """
    Combina recomendações content-based, colaborativo e popularidade.

    Args:
        user_id: usuário.
        modelo_svd: modelo SVD treinado.
        top_n: número de recomendações.
        peso_cb, peso_cf, peso_pop: pesos de cada abordagem (devem somar 1).

    Returns:
        Lista de tuplas (movie_id, score) ordenadas.
    """
    # Obtém a lista de recomendações do modelo baseado em conteúdo com o dobro de candidatos (top_n * 2)
    rec_cb = recomendar_content_based(user_id, top_n=top_n * 2)
    # Obtém a lista de recomendações do modelo colaborativo SVD com o dobro de candidatos (top_n * 2)
    rec_cf = recomendar_colaborativo(modelo_svd, user_id, top_n=top_n * 2)

    # Executa a função de cálculo de popularidade global para obter o ranking de filmes populares
    df_pop = calcular_popularidade()
    # Extrai os IDs dos filmes mais populares até o limite de top_n * 2
    filmes_populares = df_pop["movie_id"].head(top_n * 2).tolist()

    # Define a função interna auxiliar para normalizar as pontuações entre 0.0 e 1.0 (Min-Max Scaling)
    def normalizar(lista: list[tuple[int, float]]) -> dict[int, float]:
        # Se a lista estiver vazia
        if not lista:
            # Retorna um dicionário vazio
            return {}
        # Extrai os IDs dos filmes da lista de tuplas
        ids = [x[0] for x in lista]
        # Converte as pontuações em um array numpy do tipo float
        scores = np.array([x[1] for x in lista], dtype=float)
        # Se todas as pontuações forem iguais (máximo igual ao mínimo)
        if scores.max() == scores.min():
            # Atribui valor 1.0 para todos os itens para evitar divisão por zero
            norm = np.ones_like(scores)
        else:
            # Aplica a fórmula de normalização Min-Max: (x - min) / (max - min)
            norm = (scores - scores.min()) / (scores.max() - scores.min())
        # Retorna um dicionário mapeando cada ID de filme à sua pontuação normalizada
        return dict(zip(ids, norm, strict=False))

    # Normaliza as pontuações das recomendações baseadas em conteúdo
    scores_cb = normalizar(rec_cb)
    # Normaliza as pontuações das recomendações colaborativas
    scores_cf = normalizar(rec_cf)
    # Cria o dicionário de pontuações de popularidade com decaimento linear baseado na posição do ranking
    scores_pop = {
        movie_id: 1.0 - (i / len(filmes_populares))
        for i, movie_id in enumerate(filmes_populares)
    }

    # Consolida a união de todos os IDs de filmes presentes em ao menos uma das três abordagens
    todos_ids = set(scores_cb.keys()) | set(scores_cf.keys()) | set(scores_pop.keys())
    # Inicializa o dicionário onde serão armazenados os scores finais combinados por filme
    scores_finais = {}
    # Itera sobre cada ID de filme candidato único
    for movie_id in todos_ids:
        # Inicializa a pontuação ponderada do filme com 0.0
        score = 0.0
        # Se o filme estiver presente nas recomendações baseadas em conteúdo
        if movie_id in scores_cb:
            # Pondera o score pelo peso atribuído ao modelo content-based
            score += peso_cb * scores_cb[movie_id]
        # Se o filme estiver presente nas recomendações colaborativas
        if movie_id in scores_cf:
            # Pondera o score pelo peso atribuído ao modelo colaborativo
            score += peso_cf * scores_cf[movie_id]
        # Se o filme estiver presente na lista de popularidade
        if movie_id in scores_pop:
            # Pondera o score pelo peso atribuído ao modelo de popularidade
            score += peso_pop * scores_pop.get(movie_id, 0.0)
        # Registra a pontuação final ponderada acumulada para o filme
        scores_finais[movie_id] = score

    # Ordena todos os candidatos de forma decrescente pela pontuação final e seleciona os top_n primeiros
    recomendados = sorted(scores_finais.items(), key=lambda x: x[1], reverse=True)[:top_n]
    # Retorna a lista de recomendações híbridas finais
    return recomendados
