# Docstring do módulo descrevendo a avaliação unificada de todos os modelos de recomendação
"""Avaliação unificada dos modelos de recomendação."""

# Importa o módulo nativo de logging do Python para registro de métricas e status de execução
import logging

# Importa a função de carregamento de ratings, recomendação colaborativa e treino do SVD
from cinelake.recommender.collaborative import (
    carregar_ratings_surprise,
    recomendar_colaborativo,
    treinar_svd,
)

# Importa a função de recomendação baseada em conteúdo
from cinelake.recommender.content_based import recomendar_content_based

# Importa a divisão de treino/teste e a função de avaliação de popularidade do módulo evaluate
from cinelake.recommender.evaluate import (
    _dividir_treino_teste,
    avaliar_modelo_popularidade,
)

# Importa a função de recomendação híbrida
from cinelake.recommender.hybrid import recomendar_hibrido

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)


# Define a função principal de avaliação unificada dos modelos de recomendação
def avaliar_modelos(top_k: int = 10) -> dict[str, dict[str, float] | str]:
    # Docstring da função descrevendo a comparação entre popularidade, content-based, colaborativo e híbrido
    """Avalia os três modelos (popularidade, content-based, colaborativo, híbrido)."""
    # Dicionário para armazenar as métricas finais de cada modelo avaliado
    resultados: dict[str, dict[str, float] | str] = {}

    # Executa e armazena as métricas do modelo de popularidade baseline
    resultados["popularity"] = avaliar_modelo_popularidade(top_k)

    # Carrega os dados de avaliações no formato adequado para o scikit-surprise
    df = carregar_ratings_surprise()
    # Treina o modelo colaborativo SVD com os dados carregados
    modelo_svd = treinar_svd(df)

    # Executa a partição dos dados dividindo em treino e teste com corte temporal
    _, teste = _dividir_treino_teste()

    # Se o conjunto de teste estiver vazio
    if teste.empty:
        # Retorna mensagem de erro informando a ausência de dados de teste
        return {"error": "sem dados de teste"}

    # Extrai os IDs dos primeiros 20 usuários únicos do conjunto de teste para limitar o tempo de avaliação
    usuarios_teste = teste["user_id"].unique()[:20]

    # Inicializa listas e contadores de avaliação para o modelo Content-Based
    precision_cb: list[float] = []
    recall_cb: list[float] = []
    hit_cb = 0
    total_cb = 0

    # Percorre cada usuário selecionado da amostra de teste
    for user in usuarios_teste:
        # Mapeia a lista de filmes relevantes (IDs dos filmes com nota no teste) para o usuário atual
        filmes_relevantes = teste[teste["user_id"] == user]["movie_id"].tolist()
        # Gera os top_k filmes recomendados pelo modelo baseado em conteúdo
        recs = recomendar_content_based(user, top_n=top_k)
        # Extrai apenas os IDs dos filmes da lista de tuplas de recomendação
        rec_ids = [x[0] for x in recs]
        # Calcula a interseção entre filmes recomendados e filmes relevantes consumidos
        acertos = len(set(rec_ids) & set(filmes_relevantes))
        # Calcula e armazena a precisão para o usuário atual
        precision_cb.append(acertos / top_k)
        # Calcula e armazena o recall para o usuário atual
        recall_cb.append(acertos / len(filmes_relevantes) if filmes_relevantes else 0.0)
        # Incrementa a contagem de acertos (Hit) se houver ao menos 1 recomendação relevante
        hit_cb += 1 if acertos > 0 else 0
        # Incrementa o total de usuários avaliados no modelo content-based
        total_cb += 1

    # Registra o dicionário com as métricas médias obtidas pelo modelo Content-Based
    resultados["content_based"] = {
        "precision": sum(precision_cb) / total_cb if total_cb else 0.0,
        "recall": sum(recall_cb) / total_cb if total_cb else 0.0,
        "hit_rate": hit_cb / total_cb if total_cb else 0.0,
    }

    # Inicializa listas e contadores de avaliação para o modelo Colaborativo (SVD)
    precision_cf: list[float] = []
    recall_cf: list[float] = []
    hit_cf = 0
    total_cf = 0

    # Percorre cada usuário selecionado da amostra de teste
    for user in usuarios_teste:
        # Mapeia a lista de filmes relevantes para o usuário atual no conjunto de teste
        filmes_relevantes = teste[teste["user_id"] == user]["movie_id"].tolist()
        # Gera os top_k filmes recomendados pelo modelo colaborativo SVD
        recs = recomendar_colaborativo(modelo_svd, user, top_n=top_k)
        # Extrai apenas os IDs dos filmes recomendados
        rec_ids = [x[0] for x in recs]
        # Calcula a quantidade de acertos entre recomendação e teste
        acertos = len(set(rec_ids) & set(filmes_relevantes))
        # Calcula a precisão do modelo colaborativo para o usuário
        precision_cf.append(acertos / top_k)
        # Calcula o recall do modelo colaborativo para o usuário
        recall_cf.append(acertos / len(filmes_relevantes) if filmes_relevantes else 0.0)
        # Incrementa a contagem de Hit caso tenha acertado ao menos um filme
        hit_cf += 1 if acertos > 0 else 0
        # Incrementa o contador total de usuários avaliados no modelo colaborativo
        total_cf += 1

    # Registra as métricas agregadas do modelo Colaborativo SVD
    resultados["collaborative"] = {
        "precision": sum(precision_cf) / total_cf if total_cf else 0.0,
        "recall": sum(recall_cf) / total_cf if total_cf else 0.0,
        "hit_rate": hit_cf / total_cf if total_cf else 0.0,
    }

    # Inicializa listas e contadores de avaliação para o modelo Híbrido
    precision_hy: list[float] = []
    recall_hy: list[float] = []
    hit_hy = 0
    total_hy = 0

    # Percorre cada usuário selecionado da amostra de teste
    for user in usuarios_teste:
        # Mapeia a lista de filmes relevantes para o usuário atual no conjunto de teste
        filmes_relevantes = teste[teste["user_id"] == user]["movie_id"].tolist()
        # Gera os top_k filmes recomendados pelo modelo híbrido
        recs = recomendar_hibrido(user, modelo_svd, top_n=top_k)
        # Extrai apenas os IDs dos filmes recomendados
        rec_ids = [x[0] for x in recs]
        # Calcula a quantidade de acertos entre recomendação híbrida e teste
        acertos = len(set(rec_ids) & set(filmes_relevantes))
        # Calcula a precisão do modelo híbrido para o usuário
        precision_hy.append(acertos / top_k)
        # Calcula o recall do modelo híbrido para o usuário
        recall_hy.append(acertos / len(filmes_relevantes) if filmes_relevantes else 0.0)
        # Incrementa a contagem de Hit se houve ao menos 1 acerto
        hit_hy += 1 if acertos > 0 else 0
        # Incrementa o total de usuários avaliados no modelo híbrido
        total_hy += 1

    # Registra as métricas agregadas do modelo Híbrido
    resultados["hybrid"] = {
        "precision": sum(precision_hy) / total_hy if total_hy else 0.0,
        "recall": sum(recall_hy) / total_hy if total_hy else 0.0,
        "hit_rate": hit_hy / total_hy if total_hy else 0.0,
    }

    # Retorna o dicionário completo com os resultados de avaliação de todos os modelos
    return resultados
