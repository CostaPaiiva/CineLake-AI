# Docstring do módulo descrevendo que este arquivo contém os endpoints da API de recomendações
"""Endpoints de recomendações."""

# Importa o tipo Any para anotação do tipo de retorno dos endpoints
from typing import Any

# Importa APIRouter, HTTPException e Query da biblioteca FastAPI para definição de rotas, respostas de erro e validações
from fastapi import APIRouter, Query

# Importa a função text do SQLAlchemy para construção de queries SQL parametrizadas
from sqlalchemy import text

# Importa a função get_engine do módulo cinelake.db para gerenciar conexões com o banco de dados
from cinelake.db import get_engine

# Instancia o roteador do FastAPI definindo o prefixo '/recommendations' e a tag 'recommendations' para a documentação Swagger
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Define o endpoint HTTP GET na rota '/popular' com resumo explicativo para a documentação
@router.get("/popular", summary="Retorna recomendações populares")
def recomendacoes_populares(
    top_n: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retorna os filmes mais populares (baseline)."""
    engine = get_engine()
    with engine.connect() as conn:
        resultado = conn.execute(
            text("""
                SELECT movie_id, score, rank
                FROM recommendations
                WHERE model_name = 'popularity_baseline'
                  AND user_id = (SELECT MIN(user_id) FROM recommendations WHERE model_name = 'popularity_baseline')
                ORDER BY rank
                LIMIT :top_n
            """),
            {"top_n": top_n},
        ).fetchall()

    filmes = [{"movie_id": row[0], "score": row[1], "rank": row[2]} for row in resultado]
    return {"modelo": "popularity_baseline", "recomendacoes": filmes}


# Define o endpoint HTTP GET na rota '/user/{user_id}' para obter recomendações personalizadas por modelo
@router.get("/user/{user_id}", summary="Recomendações personalizadas para um usuário")
def recomendacoes_usuario(
    user_id: int,
    modelo: str = Query("hybrid", description="popularity_baseline, content_based, collaborative_item_item, hybrid"),
    top_n: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    """Retorna recomendações salvas para um usuário usando o modelo especificado."""
    engine = get_engine()
    model_key = "popularity_baseline" if modelo == "popularity" else modelo

    with engine.connect() as conn:
        resultado = conn.execute(
            text("""
                SELECT movie_id, score, rank
                FROM recommendations
                WHERE model_name = :modelo AND user_id = :user_id
                ORDER BY rank
                LIMIT :top_n
            """),
            {"modelo": model_key, "user_id": user_id, "top_n": top_n},
        ).fetchall()

    filmes = [{"movie_id": row[0], "score": row[1], "rank": row[2]} for row in resultado]
    return {"modelo": model_key, "user_id": user_id, "recomendacoes": filmes}


# Define o endpoint HTTP GET na rota '/model/{model_name}' para obter recomendações de um modelo específico salvo no banco
@router.get("/model/{model_name}", summary="Retorna recomendações de um modelo específico")
def recomendacoes_modelo(
    model_name: str,
    user_id: int | None = Query(None, description="ID do usuário; se omitido, usa o primeiro usuário"),
    top_n: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retorna recomendações de um modelo para um usuário."""
    engine = get_engine()
    with engine.connect() as conn:
        if user_id is None:
            user_id = conn.execute(
                text("SELECT MIN(user_id) FROM recommendations WHERE model_name = :modelo"),
                {"modelo": model_name},
            ).scalar()

        if user_id is None:
            return {"modelo": model_name, "user_id": None, "recomendacoes": []}

        resultado = conn.execute(
            text("""
                SELECT movie_id, score, rank
                FROM recommendations
                WHERE model_name = :modelo AND user_id = :user_id
                ORDER BY rank
                LIMIT :top_n
            """),
            {"modelo": model_name, "user_id": user_id, "top_n": top_n},
        ).fetchall()

    filmes = [{"movie_id": row[0], "score": row[1], "rank": row[2]} for row in resultado]
    return {"modelo": model_name, "user_id": user_id, "recomendacoes": filmes}
