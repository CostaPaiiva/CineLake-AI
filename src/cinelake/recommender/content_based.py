# Docstring do módulo indicando o modelo de recomendação baseado em conteúdo por gêneros
"""Modelo de recomendação baseado em conteúdo (gêneros)."""

# Importa o módulo nativo de logging do Python para registro de eventos e erros
import logging

# Importa a biblioteca numpy para operações numéricas com vetores e matrizes
import numpy as np

# Importa a biblioteca pandas para manipulação e análise de dados em DataFrames
import pandas as pd

# Importa o TfidfVectorizer do scikit-learn para conversão de texto de gêneros em matriz TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer

# Importa cosine_similarity do scikit-learn para cálculo de similaridade por cosseno entre vetores
from sklearn.metrics.pairwise import cosine_similarity

# Importa o construtor text do SQLAlchemy para execução de SQL nativo parametrizado
from sqlalchemy import text

# Importa a função get_engine do módulo cinelake.db para obter conexão com o banco de dados
from cinelake.db import get_engine

# Instancia o logger específico para este módulo usando o nome do próprio módulo (__name__)
logger = logging.getLogger(__name__)


# Define a função para carregar todos os filmes e seus gêneros cadastrados no banco de dados
def carregar_filmes() -> pd.DataFrame:
    # Docstring da função descrevendo a consulta dos filmes do banco de dados
    """Carrega filmes com gêneros do banco."""
    # Obtém o objeto Engine do SQLAlchemy configurado no projeto
    engine = get_engine()
    # Abre um bloco de conexão com o banco de dados que será fechado automaticamente
    with engine.connect() as conn:
        # Lê a tabela de filmes executando consulta SQL pura via pandas
        df = pd.read_sql("SELECT movie_id, title, genres FROM movies", conn)
    # Retorna o DataFrame com as colunas movie_id, title e genres
    return df


# Define a função para construir a matriz de similaridade entre filmes com base em seus gêneros
def construir_matriz_similaridade(df_filmes: pd.DataFrame) -> np.ndarray:
    # Docstring da função descrevendo a conversão TF-IDF e o cálculo de similaridade por cosseno
    """Constrói matriz de similaridade de cossenos entre filmes baseada nos gêneros."""
    # Converte a coluna gêneros para string única substituindo o caractere '|' por espaço
    df_filmes["generos_texto"] = df_filmes["genres"].str.replace("|", " ", regex=False)

    # Vetoriza a coluna de texto de gêneros utilizando a técnica TF-IDF e remoção de stop words em inglês
    tfidf = TfidfVectorizer(stop_words="english")
    # Ajusta o modelo e transforma o texto dos gêneros em uma matriz esparsa TF-IDF
    matriz_tfidf = tfidf.fit_transform(df_filmes["generos_texto"])

    # Calcula a matriz de similaridade por cosseno comparando todos os filmes entre si
    similaridade = cosine_similarity(matriz_tfidf, matriz_tfidf)
    # Retorna a matriz de similaridade N x N resultante
    return similaridade


# Define a função principal de recomendação baseada em conteúdo para um usuário específico
def recomendar_content_based(
    user_id: int,
    top_n: int = 10,
    filmes_avaliados: dict[int, float] | None = None,
) -> list[tuple[int, float]]:
    # Docstring da função descrevendo o algoritmo de ponderação de recomendações por histórico
    """
    Recomenda filmes similares aos que o usuário avaliou positivamente.

    Args:
        user_id: ID do usuário.
        top_n: número de recomendações.
        filmes_avaliados: dicionário opcional {movie_id: rating} para evitar consulta extra.

    Returns:
        Lista de tuplas (movie_id, score).
    """
    # Obtém o Engine de conexão com o banco de dados
    engine = get_engine()
    # Carrega a lista completa de filmes cadastrados no banco de dados
    df_filmes = carregar_filmes()
    # Calcula a matriz de similaridade de cossenos para todos os filmes carregados
    similaridade = construir_matriz_similaridade(df_filmes)

    # Se a lista de filmes avaliados foi fornecida como argumento
    if filmes_avaliados is not None:
        # Filtra apenas os filmes com nota maior ou igual a 3.5 a partir do dicionário passado
        filmes_usuario = [(movie_id, rating) for movie_id, rating in filmes_avaliados.items() if rating >= 3.5]
    else:
        # Caso contrário, conecta ao banco de dados para buscar as avaliações do usuário com nota >= 3.5
        with engine.connect() as conn:
            # Executa a consulta SQL filtrando por user_id e nota mínima 3.5
            filmes_usuario = conn.execute(
                text("SELECT movie_id, rating FROM ratings WHERE user_id = :uid AND rating >= 3.5"),
                {"uid": user_id},
            ).fetchall()

    # Se o usuário não tiver avaliações com nota suficiente
    if not filmes_usuario:
        # Retorna lista vazia pois não há histórico suficiente para personalização
        return []

    # Extrai os IDs dos filmes bem avaliados pelo usuário
    filmes_usuario_ids = [row[0] for row in filmes_usuario]
    # Encontra os índices desses filmes dentro do DataFrame df_filmes
    indices = df_filmes[df_filmes["movie_id"].isin(filmes_usuario_ids)].index.tolist()
    # Se nenhum dos filmes avaliados existir no DataFrame de filmes
    if not indices:
        # Retorna lista vazia
        return []

    # Inicializa um vetor de pontuação com zeros para todos os filmes do catálogo
    scores = np.zeros(len(df_filmes))
    # Percorre cada filme avaliado e sua respectiva nota
    for movie_id, rating in filmes_usuario:
        # Localiza o índice correspondente do filme no DataFrame df_filmes
        idx_matches = df_filmes[df_filmes["movie_id"] == movie_id].index
        # Se o filme existir no DataFrame
        if not idx_matches.empty:
            # Acumula as similaridades do filme multiplicadas pela nota do usuário
            scores += similaridade[idx_matches[0]] * float(rating)

    # Cria um conjunto (set) com os IDs dos filmes já avaliados para busca rápida O(1)
    avaliados_set = set(filmes_usuario_ids)
    # Filtra apenas os filmes que ainda não foram avaliados pelo usuário com suas respectivas pontuações
    candidatos = [
        (movie_id, score)
        for movie_id, score in zip(df_filmes["movie_id"], scores, strict=False)
        if movie_id not in avaliados_set
    ]

    # Ordena a lista de candidatos pela pontuação calculada em ordem decrescente
    candidatos.sort(key=lambda x: x[1], reverse=True)
    # Retorna os top_n primeiros filmes recomendados com melhor pontuação
    return candidatos[:top_n]
