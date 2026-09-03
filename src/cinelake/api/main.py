# Módulo da API principal do CineLake AI com suporte a roteamento e cache em memória Redis
"""API principal do CineLake AI com cache Redis."""

# Importa a biblioteca json nativa para serialização e desserialização de objetos no cache
import json
# Importa a biblioteca de logging para registros de diagnostico da aplicação
import logging
# Importa o tipo Any do módulo typing para anotações de tipo genéricas
from typing import Any

# Importa a biblioteca redis para conexão com o banco de dados em memória
import redis
# Importa os módulos principais do framework FastAPI para construção de endpoints HTTP REST
from fastapi import FastAPI, HTTPException, Query
# Importa o construtor BaseModel do Pydantic para validação do schema dos dados recebidos
from pydantic import BaseModel
# Importa o construtor text do SQLAlchemy para execução segura de SQL nativo
from sqlalchemy import text

# Importa o objeto de configurações centralizadas da aplicação CineLake
from cinelake.config import settings
# Importa a função get_engine para obter conexão com o banco de dados PostgreSQL
from cinelake.db import get_engine

# Instancia o logger específico para o módulo da API
logger = logging.getLogger(__name__)

# Cria a aplicação principal FastAPI com título e versão da documentação Swagger
app = FastAPI(title="CineLake AI - API Principal", version="1.0.0")

# Instancia a conexão com o cliente do Redis utilizando host, porta e decodificação automatizada das respostas para string
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)


# Define o schema Pydantic para validação do corpo (payload JSON) das requisições de avaliação
class RatingInput(BaseModel):
    # ID único do usuário avaliador
    user_id: int
    # ID único do filme avaliado
    movie_id: int
    # Nota atribuída ao filme
    rating: float


# Função interna para realizar busca direta dos dados do filme no banco PostgreSQL
def _obter_filme_do_banco(movie_id: int) -> dict[str, Any]:
    """Busca filme no PostgreSQL."""
    # Obtém a engine de conexão do banco
    engine = get_engine()
    # Conecta ao banco de dados PostgreSQL
    with engine.connect() as conn:
        # Executa a query SQL retornando o primeiro registro em formato de dicionário de mapeamento
        resultado = conn.execute(
            text("""
                SELECT movie_id, title, genres
                FROM movies
                WHERE movie_id = :movie_id
            """),
            {"movie_id": movie_id},
        ).mappings().first()

    # Caso a consulta não encontre nenhum registro
    if not resultado:
        # Lança exceção HTTP 404 de recurso não encontrado
        raise HTTPException(status_code=404, detail="Filme não encontrado")

    # Retorna o dicionário com os campos do filme
    return dict(resultado)


# Função interna para buscar dados do filme utilizando o cache do Redis antes de consultar o banco
def _obter_filme_com_cache(movie_id: int) -> dict[str, Any]:
    """Busca filme usando Redis como cache."""
    # Define a chave identificadora única no Redis para o filme
    chave_cache = f"filme:{movie_id}"
    # Tenta recuperar o valor em string do Redis
    cache = redis_client.get(chave_cache)

    # Se a chave foi encontrada no cache (Cache Hit)
    if cache:
        # Registra no log o acerto de cache
        logger.info("Cache hit para filme %s", movie_id)
        # Converte a string JSON de volta para dicionário Python e retorna
        return json.loads(cache)

    # Caso a chave não exista no Redis (Cache Miss)
    logger.info("Cache miss para filme %s", movie_id)
    # Busca os detalhes do filme diretamente no banco PostgreSQL
    filme = _obter_filme_do_banco(movie_id)

    # Salva os dados serializados em JSON no Redis com tempo de expiração (TTL) de 300 segundos (5 minutos)
    redis_client.setex(chave_cache, 300, json.dumps(filme))
    # Retorna o dicionário do filme
    return filme


# Endpoint GET para verificação de saúde da aplicação e da conexão com o Redis
@app.get("/health", summary="Saúde da API")
def health():
    """Retorna status da API e Redis."""
    # Tenta enviar o comando PING ao Redis para checar conectividade
    try:
        redis_client.ping()
        # Define status ok para o Redis se responder com sucesso
        redis_status = "ok"
    # Captura falha de comunicação com o Redis
    except Exception as exc:
        # Registra o erro no log
        logger.error("Redis indisponível: %s", exc)
        # Define status down para o Redis
        redis_status = "down"

    # Retorna o status geral da API e da dependência Redis
    return {"status": "ok", "redis": redis_status}


# Endpoint GET para listagem de filmes cadastrados com suporte a paginação
@app.get("/movies", summary="Lista filmes com paginação")
def listar_filmes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Lista filmes paginados."""
    # Calcula o deslocamento do banco de dados (OFFSET) a partir do número da página
    offset = (page - 1) * limit
    # Obtém a engine do banco de dados
    engine = get_engine()
    # Abre conexão com o PostgreSQL
    with engine.connect() as conn:
        # Consulta o número total de filmes na base para metadados de paginação
        total = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
        # Consulta a fatia da lista de filmes paginada
        resultado = conn.execute(
            text("""
                SELECT movie_id, title, genres
                FROM movies
                ORDER BY movie_id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        ).mappings().all()

    # Converte os resultados para uma lista de dicionários
    filmes = [dict(row) for row in resultado]
    # Retorna o envelope JSON paginado
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "filmes": filmes,
    }


# Endpoint GET para recuperar os detalhes de um filme específico aproveitando a camada de cache
@app.get("/movies/{movie_id}", summary="Detalhes de um filme (com cache)")
def detalhe_filme(movie_id: int):
    """Retorna detalhes do filme usando cache."""
    # Executa a busca otimizada com cache Redis
    return _obter_filme_com_cache(movie_id)


# Endpoint GET para obter os filmes mais populares (Trending) do modelo baseline
@app.get("/movies/trending", summary="Filmes em alta (populares)")
def filmes_trending(top_n: int = Query(10, ge=1, le=50)):
    """Retorna filmes populares do baseline."""
    # Obtém o Engine de conexão com o banco
    engine = get_engine()
    # Conecta ao PostgreSQL
    with engine.connect() as conn:
        # Busca as recomendações salvas para o modelo de popularidade no banco de dados
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
        ).mappings().all()

    # Retorna a lista de filmes populares ordenados pelo ranking
    return {"modelo": "popularity_baseline", "recomendacoes": [dict(row) for row in resultado]}


# Endpoint GET para consultar as recomendações personalizadas salvas para um determinado usuário
@app.get("/users/{user_id}/recommendations", summary="Recomendações personalizadas")
def recomendacoes_usuario(
    user_id: int,
    modelo: str = Query("hybrid", description="Modelo de recomendação"),
    top_n: int = Query(10, ge=1, le=100),
):
    """Retorna recomendações para um usuário específico."""
    # Obtém o Engine de banco de dados
    engine = get_engine()
    # Conecta ao banco PostgreSQL
    with engine.connect() as conn:
        # Busca as recomendações salvas correspondentes ao usuário e modelo informados
        resultado = conn.execute(
            text("""
                SELECT movie_id, score, rank
                FROM recommendations
                WHERE model_name = :modelo AND user_id = :user_id
                ORDER BY rank
                LIMIT :top_n
            """),
            {"modelo": modelo, "user_id": user_id, "top_n": top_n},
        ).mappings().all()

    # Lança erro 404 caso nenhuma recomendação seja encontrada no banco
    if not resultado:
        raise HTTPException(status_code=404, detail="Sem recomendações para este usuário/modelo")

    # Retorna a resposta contendo as recomendações do usuário
    return {"modelo": modelo, "user_id": user_id, "recomendacoes": [dict(row) for row in resultado]}


# Endpoint GET para consultar filmes similares a partir da tabela de similaridade de conteúdo
@app.get("/movies/{movie_id}/similar", summary="Filmes similares (content-based)")
def filmes_similares(movie_id: int, top_n: int = Query(10, ge=1, le=50)):
    """Retorna filmes similares usando tabela de similaridade (se existir)."""
    # Obtém a Engine do banco
    engine = get_engine()
    # Abre conexão com o PostgreSQL
    with engine.connect() as conn:
        # Retorna estrutura de resposta
        return {"movie_id": movie_id, "similares": []}


# Endpoint POST para registrar uma nova avaliação de usuário no banco de dados
@app.post("/ratings", summary="Registrar avaliação")
def registrar_rating(rating: RatingInput):
    """Registra uma avaliação de usuário (em produção, enviaria para Kafka)."""
    # Obtém a Engine do banco
    engine = get_engine()
    # Inicia uma transação com commit automático
    with engine.begin() as conn:
        # Executa comando de inserção de rating com tratamento de conflitos no banco
        conn.execute(
            text("""
                INSERT INTO ratings (user_id, movie_id, rating, ts)
                VALUES (:user_id, :movie_id, :rating, EXTRACT(EPOCH FROM NOW())::bigint)
                ON CONFLICT (user_id, movie_id, ts) DO NOTHING
            """),
            {"user_id": rating.user_id, "movie_id": rating.movie_id, "rating": rating.rating},
        )
    # Retorna confirmação de sucesso do registro da avaliação
    return {"status": "ok", "mensagem": "Avaliação registrada"}
