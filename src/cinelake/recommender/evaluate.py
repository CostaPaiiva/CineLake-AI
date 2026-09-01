"""Funções de avaliação offline para sistemas de recomendação."""

import logging
import pandas as pd
from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def _dividir_treino_teste(porcentagem_teste: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide ratings em treino e teste com base temporal."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ratings ORDER BY ts", conn)

    if df.empty:
        return df, df

    # Pega timestamp de corte
    corte = df["ts"].quantile(1 - porcentagem_teste)
    treino = df[df["ts"] <= corte]
    teste = df[df["ts"] > corte]

    return treino, teste


def avaliar_modelo_popularidade(top_k: int = 10) -> dict:
    """
    Avalia o modelo de popularidade usando métricas offline.

    Args:
        top_k: número de recomendações a considerar.

    Returns:
        Dicionário com métricas.
    """
    engine = get_engine()
    treino, teste = _dividir_treino_teste()

    if treino.empty or teste.empty:
        logger.warning("Dados insuficientes para avaliação")
        return {"error": "dados insuficientes"}

    # Calcula itens populares com base no treino
    media_global = treino["rating"].mean()
    min_votos = 50

    contagem = treino.groupby("movie_id").agg(
        total_votos=("rating", "count"),
        media_nota=("rating", "mean"),
    ).reset_index()

    v = contagem["total_votos"].astype(float)
    R = contagem["media_nota"].astype(float)
    m = float(min_votos)
    C = media_global

    contagem["score"] = (v / (v + m)) * R + (m / (v + m)) * C
    top_filmes = contagem.sort_values("score", ascending=False)["movie_id"].head(top_k).tolist()

    # Prepara dados de teste: filmes relevantes por usuário (nota >= 3.5)
    teste["relevante"] = (teste["rating"] >= 3.5).astype(int)
    relevantes_por_user = teste.groupby("user_id")["movie_id"].apply(list).to_dict()

    # Avalia
    precision_total = 0.0
    recall_total = 0.0
    hit = 0
    total_usuarios = 0

    for user, filmes_relevantes in relevantes_por_user.items():
        total_usuarios += 1
        # Para popularidade, os recomendados são iguais para todos
        recomendados = top_filmes
        acertos = len(set(recomendados) & set(filmes_relevantes))

        precision = acertos / len(recomendados) if recomendados else 0
        recall = acertos / len(filmes_relevantes) if filmes_relevantes else 0
        hit += 1 if acertos > 0 else 0

        precision_total += precision
        recall_total += recall

    resumo = {
        "precision_medio": precision_total / total_usuarios if total_usuarios else 0,
        "recall_medio": recall_total / total_usuarios if total_usuarios else 0,
        "hit_rate": hit / total_usuarios if total_usuarios else 0,
    }

    logger.info("Resultado da avaliação: %s", resumo)
    return resumo
