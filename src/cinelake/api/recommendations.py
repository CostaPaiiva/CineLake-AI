# Docstring do módulo descrevendo que este arquivo contém os endpoints da API de recomendações
"""Endpoints de recomendações."""

# Importa o tipo Any para anotação do tipo de retorno dos endpoints
from typing import Any

# Importa APIRouter, HTTPException e Query da biblioteca FastAPI para definição de rotas, respostas de erro e validações
from fastapi import APIRouter, HTTPException, Query

# Importa a função text do SQLAlchemy para construção de queries SQL parametrizadas
from sqlalchemy import text

# Importa a função get_engine do módulo cinelake.db para gerenciar conexões com o banco de dados
from cinelake.db import get_engine

# Importa as funções dos modelos de recomendação
from cinelake.recommender.collaborative import (
    carregar_ratings_surprise,
    recomendar_colaborativo,
    treinar_svd,
)
from cinelake.recommender.content_based import recomendar_content_based
from cinelake.recommender.hybrid import recomendar_hibrido

# Instancia o roteador do FastAPI definindo o prefixo '/recommendations' e a tag 'recommendations' para a documentação Swagger
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Define o endpoint HTTP GET na rota '/popular' com resumo explicativo para a documentação
@router.get("/popular", summary="Retorna recomendações populares")
# Define a função de controle para o endpoint aceitando o parâmetro top_n com validação e com tipo de retorno dict
def recomendacoes_populares(
    top_n: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    # Docstring da função descrevendo a finalidade da rota
    """Retorna os filmes mais populares (baseline)."""
    # Obtém o objeto Engine do banco de dados do SQLAlchemy
    engine = get_engine()
    # Abre uma conexão com o banco de dados utilizando um gerenciador de contexto
    with engine.connect() as conn:
        # Executa a consulta SQL para buscar os filmes mais populares gravados no banco pelo modelo baseline
        resultado = conn.execute(
            # Consulta SQL parametrizada selecionando os campos movie_id, score e rank
            text("""
                SELECT movie_id, score, rank
                FROM recommendations
                WHERE model_name = 'popularity_baseline'
                  AND user_id = (SELECT MIN(user_id) FROM recommendations WHERE model_name = 'popularity_baseline')
                ORDER BY rank
                LIMIT :top_n
            """),
            # Passa a quantidade limite top_n informada na requisição HTTP
            {"top_n": top_n},
        ).fetchall()  # Retorna todas as linhas da consulta

    # Mapeia as linhas retornadas em uma lista de dicionários com chaves nomeadas
    filmes = [{"movie_id": row[0], "score": row[1], "rank": row[2]} for row in resultado]
    # Retorna o objeto JSON contendo o nome do modelo utilizado e a lista dos filmes recomendados
    return {"modelo": "popularity_baseline", "recomendacoes": filmes}


# Define o endpoint HTTP GET na rota '/user/{user_id}' para obter recomendações personalizadas por modelo
@router.get("/user/{user_id}", summary="Recomendações personalizadas para um usuário")
# Define a função manipuladora da rota recebendo user_id, modelo e top_n
def recomendacoes_usuario(
    user_id: int,
    modelo: str = Query("hybrid", description="popularity, content_based, collaborative, hybrid"),
    top_n: int = Query(10, ge=1, le=50),
) -> dict[str, Any]:
    # Docstring da função descrevendo o retorno de recomendações do usuário pelo modelo especificado
    """Retorna recomendações para um usuário usando o modelo especificado."""
    # Obtém o objeto Engine do banco de dados do SQLAlchemy
    engine = get_engine()
    # Se o modelo solicitado for 'popularity'
    if modelo == "popularity":
        # Conecta ao banco de dados utilizando um gerenciador de contexto
        with engine.connect() as conn:
            # Executa a consulta SQL para buscar a lista popular no banco de dados
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
        # Mapeia as linhas retornadas em uma lista de dicionários contendo movie_id e score
        filmes = [{"movie_id": row[0], "score": row[1]} for row in resultado]
        # Retorna o objeto JSON contendo o modelo e a lista de filmes recomendados
        return {"modelo": modelo, "recomendacoes": filmes}
    # Caso o modelo seja uma das estratégias personalizadas ('content_based', 'collaborative' ou 'hybrid')
    elif modelo in ("content_based", "collaborative", "hybrid"):
        # Se o modelo exigir o algoritmo SVD treinado ('collaborative' ou 'hybrid')
        if modelo in ("collaborative", "hybrid"):
            # Carrega os dados no formato do surprise
            df = carregar_ratings_surprise()
            # Treina o modelo SVD com os dados de avaliações
            modelo_svd = treinar_svd(df)
        else:
            # Para content_based pura, o modelo SVD não é necessário
            modelo_svd = None

        # Se o modelo solicitado for 'content_based'
        if modelo == "content_based":
            # Gera as recomendações baseadas no conteúdo dos gêneros
            recs = recomendar_content_based(user_id, top_n=top_n)
        # Se o modelo solicitado for 'collaborative'
        elif modelo == "collaborative":
            # Gera as recomendações utilizando a filtragem colaborativa SVD
            recs = recomendar_colaborativo(modelo_svd, user_id, top_n=top_n)
        else:
            # Caso contrário, gera as recomendações utilizando a abordagem híbrida
            recs = recomendar_hibrido(user_id, modelo_svd, top_n=top_n)

        # Mapeia a lista de tuplas em dicionários com chaves movie_id e score
        filmes = [{"movie_id": rec[0], "score": rec[1]} for rec in recs]
        # Retorna o objeto JSON contendo o modelo e as recomendações geradas
        return {"modelo": modelo, "recomendacoes": filmes}
    else:
        # Lança exceção HTTP 400 Bad Request se um nome de modelo inválido for informado
        raise HTTPException(status_code=400, detail="Modelo inválido")


# Define o endpoint HTTP GET na rota '/model/{model_name}' para obter recomendações de um modelo específico salvo no banco
@router.get("/model/{model_name}", summary="Retorna recomendações de um modelo específico")
# Define a função manipuladora da rota recebendo model_name, user_id opcional e top_n
def recomendacoes_modelo(
    model_name: str,
    user_id: int | None = Query(None, description="ID do usuário; se omitido, usa o primeiro usuário"),
    top_n: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    # Docstring da função descrevendo a consulta de recomendações do modelo especificado
    """Retorna recomendações de um modelo para um usuário."""
    # Obtém o objeto Engine de conexão com o banco de dados
    engine = get_engine()
    # Abre um bloco de conexão com o banco de dados
    with engine.connect() as conn:
        # Se o user_id não foi informado na requisição
        if user_id is None:
            # Consulta o menor user_id cadastrado para o modelo especificado na tabela recommendations
            user_id = conn.execute(
                text("SELECT MIN(user_id) FROM recommendations WHERE model_name = :modelo"),
                {"modelo": model_name},
            ).scalar()
        # Se nenhum user_id for encontrado (modelo sem recomendações)
        if user_id is None:
            # Retorna estrutura de recomendações vazia
            return {"modelo": model_name, "user_id": None, "recomendacoes": []}

        # Executa a consulta SQL para buscar as recomendações salvas para o modelo e usuário
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

    # Mapeia as linhas retornadas em uma lista de dicionários contendo movie_id, score e rank
    filmes = [{"movie_id": row[0], "score": row[1], "rank": row[2]} for row in resultado]
    # Retorna o objeto JSON com o nome do modelo, ID do usuário e lista de filmes
    return {"modelo": model_name, "user_id": user_id, "recomendacoes": filmes}
