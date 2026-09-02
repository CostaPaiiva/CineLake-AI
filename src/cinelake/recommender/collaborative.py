# Docstring do módulo indicando que este arquivo trata do modelo de filtragem colaborativa usando SVD (scikit-surprise)
"""Modelo de filtragem colaborativa usando SVD (scikit-surprise)."""

# Importa o módulo nativo de logging do Python para registro de avisos e depuração
import logging

# Importa a biblioteca pandas para manipulação e análise de dados tabulares
import pandas as pd

# Importa a função text do SQLAlchemy para construção de instruções SQL puras parametrizadas
from sqlalchemy import text

# Importa os módulos SVD, Dataset e Reader da biblioteca scikit-surprise para filtragem colaborativa
from surprise import SVD, Dataset, Reader

# Importa a função train_test_split para eventual divisão de dados de treino e teste no scikit-surprise
from surprise.model_selection import train_test_split  # noqa: F401

# Importa a função get_engine da camada de acesso ao banco de dados do CineLake
from cinelake.db import get_engine

# Inicializa a instância do logger nomeada para o módulo atual
logger = logging.getLogger(__name__)


# Define a função para carregar dados de avaliações (ratings) no formato exigido pela biblioteca Surprise
def carregar_ratings_surprise() -> pd.DataFrame:
    # Docstring da função descrevendo a consulta e limitações de tamanho do dataset
    """Carrega ratings em formato adequado para o surprise."""
    # Obtém a instância do engine de conexão com o banco de dados
    engine = get_engine()
    # Abre um contexto de conexão gerenciado com o banco de dados
    with engine.connect() as conn:
        # Executa consulta SQL via pandas para extrair as colunas user_id, movie_id e rating da tabela ratings
        df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)

    # Verifica se a quantidade de registros excede 200.000 linhas para evitar problemas de limite de memória
    if len(df) > 200_000:
        # Registra uma mensagem de aviso no log informando a amostragem do dataset
        logger.warning("Dataset muito grande, limitando a 200k registros para demonstração")
        # Realiza uma amostragem aleatória simples de 200.000 registros fixando a semente (random_state=42)
        df = df.sample(n=200_000, random_state=42)

    # Retorna o DataFrame com as avaliações carregadas e tratadas
    return df


# Define a função para treinar o algoritmo de decomposição em valores singulares (SVD)
def treinar_svd(df: pd.DataFrame) -> SVD:
    # Docstring da função indicando a escala de notas e treinamento do modelo SVD
    """Treina modelo SVD com divisão treino/teste."""
    # Define a escala aceita para as avaliações (de 0.5 a 5.0 estrelas)
    reader = Reader(rating_scale=(0.5, 5.0))
    # Carrega a estrutura de dados do Surprise a partir do DataFrame selecionando as colunas necessárias
    data = Dataset.load_from_df(df[["user_id", "movie_id", "rating"]], reader)
    # Constrói o conjunto completo de treinamento (Trainset) incluindo todas as interações
    trainset = data.build_full_trainset()
    # Instancia o algoritmo SVD configurando 50 fatores latentes e semente aleatória reproduzível
    modelo = SVD(n_factors=50, random_state=42)
    # Executa o ajuste (fit) do modelo SVD no conjunto de treino completo
    modelo.fit(trainset)
    # Retorna o objeto do modelo SVD treinado
    return modelo


# Define a função auxiliar para estimar a nota que um usuário daria a um filme específico
def prever_rating(modelo: SVD, user_id: int, movie_id: int) -> float:
    # Docstring da função descrevendo o retorno da estimativa de nota
    """Retorna previsão de rating para um usuário e filme."""
    # Executa o método predict do Surprise e retorna apenas a estimativa numérica float (atributo 'est')
    return float(modelo.predict(user_id, movie_id).est)


# Define a função para gerar uma lista de recomendações personalizadas baseadas em filtragem colaborativa
def recomendar_colaborativo(
    modelo: SVD,
    user_id: int,
    top_n: int = 10,
    filmes_candidatos: list[int] | None = None,
) -> list[tuple[int, float]]:
    # Docstring da função descrevendo a filtragem de filmes já avaliados e ordenação por maior rating previsto
    """
    Recomenda filmes com maiores ratings previstos para um usuário.

    Args:
        modelo: modelo SVD treinado.
        user_id: ID do usuário.
        top_n: número de recomendações.
        filmes_candidatos: lista opcional de IDs a considerar; se None, usa todos os filmes.

    Returns:
        Lista de tuplas (movie_id, score).
    """
    # Se nenhuma lista de filmes candidatos foi fornecida explicitamente
    if filmes_candidatos is None:
        # Obtém a instância do engine de conexão com o banco
        engine = get_engine()
        # Conecta ao banco para buscar todos os IDs distintos de filmes cadastrados
        with engine.connect() as conn:
            # Executa a consulta SQL e mapeia a primeira coluna de cada linha para uma lista de inteiros
            filmes_candidatos = [
                row[0] for row in conn.execute(text("SELECT DISTINCT movie_id FROM movies")).fetchall()
            ]

    # Obtém o engine de banco de dados para consultar o histórico do usuário
    engine = get_engine()
    # Conecta ao banco de dados para recuperar os filmes já avaliados por este usuário específico
    with engine.connect() as conn:
        # Cria um conjunto (set) contendo os IDs dos filmes avaliados para otimização de busca O(1)
        avaliados = {
            row[0]
            for row in conn.execute(
                text("SELECT movie_id FROM ratings WHERE user_id = :uid"), {"uid": user_id}
            ).fetchall()
        }

    # Filtra a lista de candidatos mantendo apenas aqueles que ainda não foram avaliados pelo usuário
    candidatos_filtrados = [m for m in filmes_candidatos if m not in avaliados]

    # Inicializa uma lista vazia para armazenar as tuplas com previsões (movie_id, score_previsto)
    previsoes = []
    # Itera sobre cada filme candidato elegível
    for movie_id in candidatos_filtrados:
        try:
            # Calcula a previsão de nota para o par (user_id, movie_id) utilizando a função prever_rating
            est = prever_rating(modelo, user_id, movie_id)
            # Adiciona a tupla (movie_id, nota_estimada) na lista de previsões
            previsoes.append((movie_id, est))
        # Captura eventuais exceções durante a estimativa de um filme individual
        except Exception as exc:
            # Registra uma mensagem de aviso no log detalhando a falha ocorrida
            logger.warning("Erro ao prever para (%d,%d): %s", user_id, movie_id, exc)

    # Ordena a lista de previsões com base no score previsto (índice 1 da tupla) em ordem decrescente
    previsoes.sort(key=lambda x: x[1], reverse=True)
    # Retorna os top_n primeiros filmes recomendados
    return previsoes[:top_n]
