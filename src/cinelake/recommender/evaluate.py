# Docstring do módulo descrevendo o objetivo de conter funções de avaliação offline
"""Funções de avaliação offline para sistemas de recomendação."""

# Importa o módulo nativo de logging para registro de mensagens no console/arquivo
import logging

# Importa o tipo Any para anotações de tipagem genérica
from typing import Any

# Importa a biblioteca pandas para manipulação e análise de DataFrames
import pandas as pd

# Importa a função get_engine do banco de dados do projeto CineLake
from cinelake.db import get_engine

# Instancia o logger com o nome do módulo corrente
logger = logging.getLogger(__name__)


# Função interna privada para realizar a divisão dos dados entre treino e teste por ordenação temporal
def _dividir_treino_teste(porcentagem_teste: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Docstring da função interna de partição de dados
    """Divide ratings em treino e teste com base temporal."""
    # Obtém o Engine de conexão com o banco de dados
    engine = get_engine()
    # Conecta ao banco de dados utilizando um bloco de contexto
    with engine.connect() as conn:
        # Lê toda a tabela ratings ordenada cronologicamente pelo timestamp 'ts'
        df = pd.read_sql("SELECT * FROM ratings ORDER BY ts", conn)

    # Caso não existam dados na tabela ratings
    if df.empty:
        # Retorna dois DataFrames vazios
        return df, df

    # Calcula o ponto de corte do timestamp usando o percentil desejado (ex: 80% treino / 20% teste)
    corte = df["ts"].quantile(1 - porcentagem_teste)
    # Filtra os registros com timestamp menor ou igual ao ponto de corte para treino
    treino = df[df["ts"] <= corte]
    # Filtra os registros com timestamp maior que o ponto de corte para teste
    teste = df[df["ts"] > corte]

    # Retorna a tupla contendo o conjunto de treino e o conjunto de teste
    return treino, teste


# Função pública para realizar a avaliação offline das recomendações por popularidade
def avaliar_modelo_popularidade(top_k: int = 10) -> dict[str, Any]:
    # Docstring da função indicando o cálculo de métricas offline
    """
    Avalia o modelo de popularidade usando métricas offline.

    Args:
        top_k: número de recomendações a considerar.

    Returns:
        Dicionário com métricas.
    """
    # Executa a partição dos dados obtendo os DataFrames de treino e teste
    treino, teste = _dividir_treino_teste()

    # Caso um dos dois DataFrames esteja vazio devido a falta de registros
    if treino.empty or teste.empty:
        # Grava mensagem de aviso no logger
        logger.warning("Dados insuficientes para avaliação")
        # Retorna dicionário com sinalização de erro de dados insuficientes
        return {"error": "dados insuficientes"}

    # Calcula a média de todas as notas presentes apenas no conjunto de treino (C)
    media_global = treino["rating"].mean()
    # Define o número mínimo de avaliações considerado para a constante m da fórmula
    min_votos = 50

    # Agrupa o conjunto de treino por filme e calcula contagem total de votos e média das notas
    contagem = treino.groupby("movie_id").agg(
        # Calcula a contagem total de votos por filme
        total_votos=("rating", "count"),
        # Calcula a média das notas por filme
        media_nota=("rating", "mean"),
    ).reset_index()  # Restaura o movie_id de índice para coluna comum

    # Converte o total de votos para tipo float (v)
    v = contagem["total_votos"].astype(float)
    # Converte a média de notas para tipo float (R da fórmula IMDB)
    R = contagem["media_nota"].astype(float)  # noqa: N806
    # Converte o mínimo de votos para tipo float (m da fórmula IMDB)
    m = float(min_votos)
    # Atribui a média global calculada à variável C (constante IMDB)
    C = media_global  # noqa: N806

    # Calcula o score de popularidade ponderada usando os dados do treino
    contagem["score"] = (v / (v + m)) * R + (m / (v + m)) * C
    # Seleciona os top_k filmes de maior score e extrai apenas a lista com seus movie_ids
    top_filmes = contagem.sort_values("score", ascending=False)["movie_id"].head(top_k).tolist()

    # Cria coluna booleana no teste identificando itens relevantes (nota maior ou igual a 3.5)
    teste["relevante"] = (teste["rating"] >= 3.5).astype(int)
    # Agrupa por usuário e mapeia os filmes relevantes que cada usuário consumiu no conjunto de teste
    relevantes_por_user = teste.groupby("user_id")["movie_id"].apply(list).to_dict()

    # Inicializa acumulador da precisão total dos usuários
    precision_total = 0.0
    # Inicializa acumulador da revocação (recall) total dos usuários
    recall_total = 0.0
    # Inicializa contador de acertos no Hit Rate (usuários que tiveram ao menos 1 acerto)
    hit = 0
    # Inicializa contador de total de usuários avaliados
    total_usuarios = 0

    # Itera sobre cada usuário (ignorando o id com _user) e sua respectiva lista de filmes relevantes do teste
    for _user, filmes_relevantes in relevantes_por_user.items():
        # Incrementa o número total de usuários avaliados
        total_usuarios += 1
        # Atribui a lista top_filmes calculada às recomendações do usuário
        recomendados = top_filmes
        # Calcula o número de acertos (interseção entre filmes recomendados e os que o usuário gostou)
        acertos = len(set(recomendados) & set(filmes_relevantes))

        # Calcula a precisão do usuário (acertos divididos pela quantidade de itens recomendados)
        precision = acertos / len(recomendados) if recomendados else 0
        # Calcula o recall do usuário (acertos divididos pela quantidade total de itens relevantes do usuário)
        recall = acertos / len(filmes_relevantes) if filmes_relevantes else 0
        # Incrementa o contador de hit se o usuário teve pelo menos 1 recomendação acertada
        hit += 1 if acertos > 0 else 0

        # Acumula a precisão individual do usuário na soma total
        precision_total += precision
        # Acumula o recall individual do usuário na soma total
        recall_total += recall

    # Monta o dicionário de resultado com as médias gerais calculadas
    resumo = {
        # Calcula a média da precisão entre todos os usuários
        "precision_medio": precision_total / total_usuarios if total_usuarios else 0,
        # Calcula a média do recall entre todos os usuários
        "recall_medio": recall_total / total_usuarios if total_usuarios else 0,
        # Calcula a taxa geral de acerto (hit rate) entre os usuários
        "hit_rate": hit / total_usuarios if total_usuarios else 0,
    }

    # Registra no log o resultado final das métricas da avaliação
    logger.info("Resultado da avaliação: %s", resumo)
    # Retorna o dicionário de resumo das métricas
    return resumo
