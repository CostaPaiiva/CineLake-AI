"""Comparação entre acesso ao banco com e sem Redis."""

# Importa o módulo json da biblioteca padrão para serialização e deserialização dos dados em cache
import json
# Importa o módulo nativo de logging do Python para emissão de mensagens informativas e de diagnóstico
import logging
# Importa o módulo nativo time para realizar a medição precisa do tempo de resposta das operações
import time
# Importa Any do módulo typing para anotações de tipos genéricos
from typing import Any

# Importa o cliente da biblioteca redis para comunicação com o banco em memória Redis
import redis
# Importa a função text do SQLAlchemy para construção e execução de consultas SQL estruturadas
from sqlalchemy import text

# Importa as configurações centralizadas da aplicação CineLake
from cinelake.config import settings
# Importa a função de conexão para obter a Engine do PostgreSQL
from cinelake.db import get_engine

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Função responsável por comparar o tempo de resposta do acesso a dados diretamente no PostgreSQL versus cache Redis
def benchmark_redis_vs_no_redis(movie_id: int, repeticoes: int = 5) -> dict[str, Any]:
    """Compara latência de acesso a um filme com e sem Redis."""
    # Registra no log o início da execução do benchmark comparativo
    logger.info("Benchmark Redis x sem Redis")
    # Inicializa a Engine de conexão com o banco de dados relacional
    engine = get_engine()
    # Cria a instância do cliente de conexão com o servidor Redis com decodificação automática de strings
    cliente = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    # Define a chave de cache estruturada para o identificador do filme
    chave = f"bench_filme:{movie_id}"

    # Garante cache limpo
    # Remove a chave do Redis antes do teste para garantir um estado inicial sem cache prévio
    cliente.delete(chave)

    # Lista para registrar os tempos de resposta das consultas diretas ao banco sem cache
    tempos_sem = []
    # Lista para registrar os tempos de resposta das leituras realizadas a partir do cache Redis
    tempos_com = []

    # Executa a consulta direta no PostgreSQL repetidas vezes para medir o tempo médio
    for _ in range(repeticoes):
        # Sem Redis
        # Marca o tempo inicial antes de abrir a conexão e disparar a query no banco
        inicio = time.time()
        # Abre uma conexão com o pool do banco de dados relacional
        with engine.connect() as conn:
            # Executa a query SQL buscando as informações do filme pelo seu ID
            conn.execute(
                # Declaração SQL com parâmetro bind :id para busca indexada/filtrada
                text("SELECT movie_id, title, genres FROM movies WHERE movie_id = :id"),
                # Dicionário com os parâmetros passados com segurança para a query
                {"id": movie_id},
            ).mappings().first()
        # Calcula o tempo total da operação no banco e adiciona à lista de tempos sem Redis
        tempos_sem.append(time.time() - inicio)

    # Popula cache
    # Realiza a consulta uma única vez no banco de dados para extrair o registro do filme
    with engine.connect() as conn:
        # Executa a consulta SQL e recupera a linha como dicionário mapeado
        linha = conn.execute(
            text("SELECT movie_id, title, genres FROM movies WHERE movie_id = :id"),
            {"id": movie_id},
        ).mappings().first()
    # Verifica se o filme foi encontrado no banco de dados
    if linha:
        # Armazena os dados do filme em formato JSON no Redis com tempo de expiração (TTL) de 300 segundos
        cliente.setex(chave, 300, json.dumps(dict(linha)))

    # Executa a leitura a partir da memória do Redis repetidas vezes para medir a latência
    for _ in range(repeticoes):
        # Com Redis
        # Marca o tempo inicial antes de consultar o cache na memória
        inicio = time.time()
        # Busca o valor da chave diretamente no servidor Redis
        cache = cliente.get(chave)
        # Verifica se o dado foi recuperado com sucesso do cache (cache hit)
        if cache:
            # Deserializa a string JSON convertendo-a de volta para um dicionário Python
            _ = json.loads(cache)
        # Calcula o tempo total da operação de leitura em memória e adiciona à lista
        tempos_com.append(time.time() - inicio)

    # Limpa a chave de cache utilizada após o término das medições do teste
    cliente.delete(chave)

    # Retorna o dicionário consolidado contendo todas as métricas apuradas no benchmark
    return {
        # Identificador do tipo de benchmark executado
        "benchmark": "redis_vs_no_redis",
        # ID do filme consultado durante o teste
        "movie_id": movie_id,
        # Tempo médio em segundos para consultas diretas ao PostgreSQL (com 6 casas decimais)
        "tempo_medio_sem_redis_s": round(sum(tempos_sem) / len(tempos_sem), 6),
        # Tempo médio em segundos para leituras em cache na memória do Redis (com 6 casas decimais)
        "tempo_medio_com_redis_s": round(sum(tempos_com) / len(tempos_com), 6),
        # Porcentagem de ganho de performance/velocidade obtida com o uso do Redis
        "ganho_pct": round(
            # Fórmula matemática de cálculo do percentual de ganho de tempo
            (1 - sum(tempos_com) / sum(tempos_sem)) * 100, 2
        ) if sum(tempos_sem) > 0 else 0,
    }
