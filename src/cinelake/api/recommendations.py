# Docstring do módulo descrevendo que este arquivo contém os endpoints da API de recomendações
"""Endpoints de recomendações."""

# Importa as classes APIRouter e Query da biblioteca FastAPI para definição de rotas e validações de parâmetros
from fastapi import APIRouter, Query
# Importa a função text do SQLAlchemy para construção de queries SQL parametrizadas
from sqlalchemy import text

# Importa a função get_engine do módulo cinelake.db para gerenciar conexões com o banco de dados
from cinelake.db import get_engine

# Instancia o roteador do FastAPI definindo o prefixo '/recommendations' e a tag 'recommendations' para a documentação Swagger
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Define o endpoint HTTP GET na rota '/popular' com resumo explicativo para a documentação
@router.get("/popular", summary="Retorna recomendações populares")
# Define a função de controle para o endpoint aceitando o parâmetro top_n com validação (entre 1 e 100, valor padrão 10)
def recomendacoes_populares(
    top_n: int = Query(10, ge=1, le=100),
):
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
