# Docstring do módulo indicando o modelo de recomendação baseado em conteúdo usando gêneros
"""Modelo de recomendação baseado em conteúdo usando gêneros."""

# Importa o módulo nativo de logging do Python para registro de eventos e avisos
import logging

# Importa datetime e timezone do módulo nativo datetime para datas UTC
from datetime import datetime, timezone

# Importa a biblioteca numpy para operações matriciais e numéricas
import numpy as np

# Importa a biblioteca pandas para manipulação e análise de dados em DataFrames
import pandas as pd

# Importa a função cosine_similarity do scikit-learn para calcular a similaridade por cosseno
from sklearn.metrics.pairwise import cosine_similarity

# Importa a função text do SQLAlchemy para construção de queries SQL puras parametrizadas
from sqlalchemy import text

# Importa a função get_engine da camada de acesso ao banco de dados do CineLake
from cinelake.db import get_engine
# Importa a função para log de parâmetros e métricas no MLflow
from cinelake.mlops.tracking import log_parametros_e_metricas

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)

# Define a constante global com o nome do modelo utilizado na gravação da tabela de recomendações
MODEL_NAME = "content_based"


# Função interna privada para carregar os dados de filmes e gêneros do banco PostgreSQL
def _carregar_dados() -> pd.DataFrame:
    # Docstring da função descrevendo a consulta SQL dos filmes
    """Carrega filmes e gêneros do PostgreSQL."""
    # Obtém o objeto Engine de conexão com o banco de dados
    engine = get_engine()
    # Abre um bloco de conexão com o banco que será fechado automaticamente ao final
    with engine.connect() as conn:
        # Lê do banco as colunas movie_id e genres da tabela movies utilizando pandas
        df = pd.read_sql("SELECT movie_id, genres FROM movies", conn)
    # Retorna o DataFrame contendo os dados dos filmes
    return df


# Função interna privada para converter a coluna genres em uma matriz binária one-hot encoding
def _criar_matriz_generos(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    # Docstring da função descrevendo a transformação dos gêneros em representação vetorial binária
    """Converte a coluna genres em one-hot encoding."""
    # Separa os gêneros delimitados pelo caractere '|' criando uma lista de gêneros por filme
    generos_por_filme = df["genres"].str.split("|")
    # Extrai e ordena a lista única de todos os gêneros válidos presentes nos filmes
    todos_generos = sorted(set(g for lista in generos_por_filme for g in lista if g))

    # Cria uma matriz binária preenchida com zeros de dimensões (número de filmes x número de gêneros)
    matriz = np.zeros((len(df), len(todos_generos)), dtype=int)
    # Percorre cada filme e sua respectiva lista de gêneros
    for i, generos in enumerate(generos_por_filme):
        # Percorre cada gênero do filme atual
        for genero in generos:
            # Se o gênero não for uma string vazia
            if genero:
                # Obtém o índice correspondente do gênero na lista ordenada
                j = todos_generos.index(genero)
                # Define a posição (i, j) na matriz binária com o valor 1
                matriz[i, j] = 1

    # Retorna o DataFrame contendo os movie_ids e a matriz binária de gêneros
    return df[["movie_id"]], matriz


# Função pública para calcular a matriz de similaridade de cossenos item-item baseada nos gêneros
def calcular_similaridade_itens() -> pd.DataFrame:
    # Docstring da função descrevendo o cálculo da matriz de similaridade entre pares de filmes
    """Calcula similaridade de cossenos entre filmes baseado em gêneros."""
    # Carrega os dados de filmes do banco de dados
    df = _carregar_dados()
    # Caso o DataFrame de filmes esteja vazio
    if df.empty:
        # Retorna um DataFrame vazio com as colunas apropriadas
        return pd.DataFrame(columns=["movie_id_1", "movie_id_2", "similaridade"])

    # Cria a matriz binária de gêneros para os filmes carregados
    df_ids, matriz = _criar_matriz_generos(df)
    # Calcula a similaridade por cosseno entre todas as combinações de filmes
    similaridade = cosine_similarity(matriz)

    # Extrai os IDs dos filmes em formato de lista
    ids = df_ids["movie_id"].tolist()
    # Inicializa a lista de dicionários para armazenar as linhas do DataFrame resultante
    linhas = []
    # Percorre a matriz de similaridade extraindo os pares únicos (triângulo superior)
    for i in range(len(ids)):
        # Itera sobre os índices j superiores a i para evitar pares duplicados e auto-similaridade
        for j in range(i + 1, len(ids)):
            # Adiciona o par de filmes e seu score de similaridade à lista
            linhas.append(
                {
                    # Atribui o ID do primeiro filme do par
                    "movie_id_1": ids[i],
                    # Atribui o ID do segundo filme do par
                    "movie_id_2": ids[j],
                    # Atribui a pontuação de similaridade convertida para float
                    "similaridade": float(similaridade[i, j]),
                }
            )
    # Retorna o DataFrame contendo os pares de filmes e suas respectivas similaridades
    return pd.DataFrame(linhas)


# Função pública para gerar e gravar as recomendações content-based na tabela recommendations
def gerar_recomendacoes_content_based(
    top_n: int = 100,
    usuario_referencia: int | None = None,
) -> None:
    # Docstring da função detalhando o processo de recomendação em lote por histórico de avaliações
    """
    Gera recomendações content-based para cada usuário (ou para um usuário específico).

    Para cada usuário, recomenda filmes similares aos que ele avaliou positivamente (rating >= 3.5).

    Args:
        top_n: número máximo de recomendações por usuário.
        usuario_referencia: se fornecido, gera apenas para esse usuário.
    """
    # Obtém a instância de conexão com o banco de dados
    engine = get_engine()
    # Conecta ao banco de dados para recuperar as avaliações positivas e a lista de usuários
    with engine.connect() as conn:
        # Lê apenas as avaliações com nota maior ou igual a 3.5
        ratings = pd.read_sql(
            text("""
                SELECT user_id, movie_id, rating
                FROM ratings
                WHERE rating >= 3.5
            """),
            conn,
        )
        # Lê a lista de todos os usuários distintos cadastrados na tabela de avaliações
        usuarios = pd.read_sql("SELECT DISTINCT user_id FROM ratings", conn)

    # Se um usuário de referência específico foi informado como parâmetro
    if usuario_referencia:
        # Filtra o DataFrame de usuários mantendo apenas o usuário especificado
        usuarios = usuarios[usuarios["user_id"] == usuario_referencia]

    # Se não houver dados de avaliações ou usuários disponíveis
    if ratings.empty or usuarios.empty:
        # Registra um aviso no log
        logger.warning("Dados insuficientes")
        # Encerra a execução da função
        return

    # Executa o cálculo da matriz de similaridades item-item
    df_similaridade = calcular_similaridade_itens()
    # Se a tabela de similaridades estiver vazia
    if df_similaridade.empty:
        # Encerra a execução
        return

    # Constrói o dicionário de similaridades mapeando cada filme para sua lista de (filme_similar, score)
    similaridade_dict: dict[int, list[tuple[int, float]]] = {}
    # Itera sobre cada linha da tabela de similaridade de filmes
    for _, row in df_similaridade.iterrows():
        # Extrai o ID do primeiro filme
        id1 = int(row["movie_id_1"])
        # Extrai o ID do segundo filme
        id2 = int(row["movie_id_2"])
        # Extrai a pontuação de similaridade
        sim = float(row["similaridade"])
        # Adiciona a relação simétrica no dicionário para id1 -> id2
        similaridade_dict.setdefault(id1, []).append((id2, sim))
        # Adiciona a relação simétrica no dicionário para id2 -> id1
        similaridade_dict.setdefault(id2, []).append((id1, sim))

    # Inicializa a lista de dicionários para armazenar os registros das recomendações geradas
    registros = []
    # Itera sobre a lista de IDs de usuários
    for user_id in usuarios["user_id"].tolist():
        # Obtém a lista dos IDs dos filmes que o usuário avaliou positivamente
        filmes_gostados = ratings[ratings["user_id"] == user_id]["movie_id"].tolist()
        # Dicionário local para acumular as pontuações dos filmes recomendados
        scores: dict[int, float] = {}
        # Percorre cada filme que o usuário gostou
        for filme in filmes_gostados:
            # Obtém a lista de filmes similares a este filme gostado
            similares = similaridade_dict.get(filme, [])
            # Percorre cada filme similar e seu grau de similaridade
            for similar, sim in similares:
                # Garante que o filme similar ainda não foi assistido/avaliado pelo usuário
                if similar not in filmes_gostados:
                    # Acumula o score de similaridade para o filme recomendado
                    scores[similar] = scores.get(similar, 0.0) + sim

        # Ordena os filmes recomendados por score em ordem decrescente e pega os top_n primeiros
        filmes_recomendados = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        # Inicializa o ranking do usuário iniciando na posição 1
        rank = 1
        # Percorre a lista dos filmes recomendados e suas pontuações
        for movie_id, score in filmes_recomendados:
            # Adiciona o registro com os dados da recomendação à lista
            registros.append(
                {
                    # Atribui o ID do usuário
                    "user_id": user_id,
                    # Atribui o ID do filme recomendado
                    "movie_id": movie_id,
                    # Atribui a pontuação final calculada
                    "score": float(score),
                    # Atribui a posição no ranking
                    "rank": rank,
                    # Atribui o nome do modelo 'content_based'
                    "model_name": MODEL_NAME,
                    # Atribui o timestamp UTC atual
                    "created_at": datetime.now(timezone.utc),
                }
            )
            # Incrementa o rank para a próxima recomendação do mesmo usuário
            rank += 1

    # Se foram geradas recomendações
    if registros:
        # Converte a lista de registros para um DataFrame do pandas
        df_rec = pd.DataFrame(registros)
        # Abre um bloco de transação no banco de dados com autocommit ao final
        with engine.begin() as conn:
            # Remove as recomendações anteriores geradas por este mesmo modelo
            conn.execute(
                text("DELETE FROM recommendations WHERE model_name = :modelo"),
                {"modelo": MODEL_NAME},
            )
            # Insere as novas recomendações na tabela 'recommendations'
            df_rec.to_sql(
                "recommendations",
                conn,
                if_exists="append",
                index=False,
                method="multi",
            )

        # Bloco try/except para avaliação offline do modelo e registro das métricas no MLflow
        try:
            # Importação local para evitar importação circular
            from cinelake.recommender.evaluate import avaliar_modelo
            # Executa a avaliação offline do modelo content_based
            metricas = avaliar_modelo(MODEL_NAME, top_k=10)
            # Registra no MLflow os parâmetros e métricas obtidas
            log_parametros_e_metricas(
                experimento_nome="recommendations",
                parametros={"modelo": MODEL_NAME, "top_n": top_n},
                metricas=metricas,
            )
        except Exception as e:
            # Registra aviso no log caso falhe a comunicação com MLflow
            logger.warning("Falha ao registrar no MLflow: %s", e)

        # Grava no log o sucesso da geração de recomendações
        logger.info("Content-based: recomendações geradas para %d usuários", len(usuarios))
    else:
        # Registra um aviso no log informando que nenhuma recomendação foi gerada
        logger.warning("Content-based: nenhuma recomendação gerada")
