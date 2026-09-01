"""Modelo de recomendação baseline por popularidade."""

import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def calcular_popularidade(min_votos: int = 50) -> pd.DataFrame:
    """
    Calcula score de popularidade ponderada para cada filme.

    Fórmula: (v/(v+m))*R + (m/(v+m))*C

    Args:
        min_votos: mínimo de votos para considerar o filme (m).

    Returns:
        DataFrame com colunas: movie_id, score_popularidade, total_votos, media_nota.
    """
    engine = get_engine()
    with engine.connect() as conn:
        # Média global (C)
        media_global = conn.execute(
            text("SELECT AVG(rating) FROM ratings")
        ).scalar()
        media_global = float(media_global) if media_global else 0.0

        # Agregação por filme: total de votos (v) e média (R)
        df = pd.read_sql(
            text("""
                SELECT movie_id, COUNT(*) AS total_votos, AVG(rating) AS media_nota
                FROM ratings
                GROUP BY movie_id
            """),
            conn,
        )

    if df.empty:
        return df

    # Aplica fórmula de popularidade ponderada
    v = df["total_votos"].astype(float)
    R = df["media_nota"].astype(float)
    m = float(min_votos)
    C = media_global

    df["score_popularidade"] = (v / (v + m)) * R + (m / (v + m)) * C
    df = df.sort_values("score_popularidade", ascending=False)

    return df


def gerar_recomendacoes_populares(top_n: int = 100, modelo: str = "popularity_baseline") -> None:
    """
    Gera recomendações populares para todos os usuários (não personalizado).

    Args:
        top_n: número de recomendações por usuário.
        modelo: nome do modelo para gravação.
    """
    engine = get_engine()
    df_populares = calcular_popularidade()

    if df_populares.empty:
        logger.warning("Sem dados para gerar recomendações populares")
        return

    top_filmes = df_populares.head(top_n)["movie_id"].tolist()

    # Obtém todos os usuários únicos
    with engine.connect() as conn:
        usuarios = [row[0] for row in conn.execute(text("SELECT DISTINCT user_id FROM ratings")).fetchall()]

    if not usuarios:
        logger.warning("Nenhum usuário encontrado")
        return

    # Monta DataFrame de recomendações
    registros = []
    rank = 1
    for user in usuarios:
        for movie_id in top_filmes:
            registros.append(
                {
                    "user_id": user,
                    "movie_id": movie_id,
                    "score": 1.0,  # score igual para todos (popularidade pura)
                    "rank": rank,
                    "model_name": modelo,
                    "created_at": datetime.now(timezone.utc),
                }
            )
            rank += 1
        rank = 1

    df_rec = pd.DataFrame(registros)

    # Grava na tabela
    with engine.begin() as conn:
        # Limpa recomendações anteriores do modelo
        conn.execute(
            text("DELETE FROM recommendations WHERE model_name = :modelo"),
            {"modelo": modelo},
        )
        # Insere novas
        df_rec.to_sql(
            "recommendations",
            conn,
            if_exists="append",
            index=False,
            method="multi",
        )

    logger.info("Recomendações populares geradas para %d usuários", len(usuarios))
