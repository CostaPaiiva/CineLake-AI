# Docstring do módulo indicando o modelo de recomendação colaborativa item-item baseado em ratings
"""Modelo de recomendação colaborativa item-item baseado em ratings."""

# Importa o módulo nativo de logging do Python para registro de diagnósticos e avisos
import logging

# Importa datetime e timezone para manipulação de datas e horas em padrão UTC
from datetime import datetime, timezone

# Importa a biblioteca numpy para operações matriciais e numéricas
# Importa a biblioteca pandas para manipulação e estruturação de DataFrames
import pandas as pd

# Importa a função cosine_similarity do scikit-learn para calcular a similaridade de cossenos entre itens
from sklearn.metrics.pairwise import cosine_similarity

# Importa a função text do SQLAlchemy para construção de instruções SQL puras parametrizadas
from sqlalchemy import text

# Importa a função get_engine da camada de acesso ao banco de dados do CineLake
from cinelake.db import get_engine

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)

# Define a constante global contendo o identificador do modelo gravado na tabela de recomendações
MODEL_NAME = "collaborative_item_item"


# Função interna privada para carregar as avaliações do banco e construir a matriz usuário x item
def _carregar_matriz_usuarios_itens() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Docstring da função descrevendo a transformação dos ratings em matriz pivô
    """Carrega ratings e pivota em matriz usuário x item."""
    # Obtém o objeto Engine de conexão com o banco de dados
    engine = get_engine()
    # Abre um bloco de conexão gerenciada com o banco de dados
    with engine.connect() as conn:
        # Lê a tabela de avaliações extraindo user_id, movie_id e rating
        df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)

    # Se a tabela de avaliações estiver vazia
    if df.empty:
        # Retorna dois DataFrames vazios
        return pd.DataFrame(), pd.DataFrame()

    # Transforma o DataFrame de ratings em matriz pivô (usuários nas linhas, filmes nas colunas, prenchendo ausentes com 0)
    matriz = df.pivot_table(index="user_id", columns="movie_id", values="rating", fill_value=0)
    # Retorna a matriz pivô e o DataFrame resumido de interações
    return matriz, df[["user_id", "movie_id"]]


# Função pública para calcular a similaridade de cossenos entre filmes com base nos perfis dos usuários
def calcular_similaridade_itens_colaborativa() -> pd.DataFrame:
    # Docstring da função descrevendo o cálculo da matriz de similaridade item-item
    """
    Calcula similaridade item-item usando cossenos entre as colunas da matriz usuário-item.
    """
    # Carrega a matriz pivô usuário-item
    matriz, _ = _carregar_matriz_usuarios_itens()
    # Se a matriz pivô estiver vazia
    if matriz.empty:
        # Retorna um DataFrame vazio com a estrutura de colunas apropriada
        return pd.DataFrame(columns=["movie_id_1", "movie_id_2", "similaridade"])

    # Calcula a similaridade de cossenos entre as colunas da matriz (transposta de matriz)
    similaridade = cosine_similarity(matriz.T)
    # Extrai a lista de IDs de todos os filmes presentes nas colunas da matriz pivô
    ids_itens = matriz.columns.tolist()

    # Inicializa a lista de dicionários para armazenar os pares de similaridade
    linhas = []
    # Percorre os índices de itens para extrair o triângulo superior da matriz de similaridades
    for i in range(len(ids_itens)):
        # Itera sobre os índices j estritamente maiores que i para evitar duplicidade
        for j in range(i + 1, len(ids_itens)):
            # Adiciona a tupla de similaridade entre o par de filmes à lista
            linhas.append(
                {
                    # Atribui o ID do primeiro filme
                    "movie_id_1": ids_itens[i],
                    # Atribui o ID do segundo filme
                    "movie_id_2": ids_itens[j],
                    # Atribui a pontuação de similaridade entre eles convertida para float
                    "similaridade": float(similaridade[i, j]),
                }
            )
    # Retorna o DataFrame com as pontuações de similaridade entre todos os pares de filmes
    return pd.DataFrame(linhas)


# Função pública para gerar e gravar as recomendações colaborativas item-item no banco de dados
def gerar_recomendacoes_colaborativas(
    top_n: int = 100,
    usuario_referencia: int | None = None,
) -> None:
    # Docstring da função detalhando o cálculo de score ponderado por similaridade entre itens
    """
    Gera recomendações colaborativas para cada usuário (ou um específico).

    Para cada usuário, calcula score dos itens não avaliados como soma ponderada
    dos ratings que ele deu, multiplicados pela similaridade entre itens.

    Args:
        top_n: número máximo de recomendações por usuário.
        usuario_referencia: se fornecido, gera apenas para esse usuário.
    """
    # Obtém o objeto Engine de conexão com o banco de dados
    engine = get_engine()
    # Carrega a matriz pivô usuário-item do banco
    matriz, _ = _carregar_matriz_usuarios_itens()
    # Se a matriz pivô estiver vazia
    if matriz.empty:
        # Registra um aviso no log
        logger.warning("Matriz vazia")
        # Encerra a execução da função
        return

    # Calcula a tabela de similaridades colaborativas entre os filmes
    df_similaridade = calcular_similaridade_itens_colaborativa()
    # Se a tabela de similaridades estiver vazia
    if df_similaridade.empty:
        # Encerra a execução
        return

    # Constrói o dicionário de similaridades mapeando cada filme para sua lista de (filme_similar, sim)
    sim_dict: dict[int, list[tuple[int, float]]] = {}
    # Itera sobre as linhas da tabela de similaridade
    for _, row in df_similaridade.iterrows():
        # Extrai o ID do primeiro filme
        id1 = int(row["movie_id_1"])
        # Extrai o ID do segundo filme
        id2 = int(row["movie_id_2"])
        # Extrai o valor da similaridade por cosseno
        sim = float(row["similaridade"])
        # Registra a similaridade simétrica para id1 -> id2
        sim_dict.setdefault(id1, []).append((id2, sim))
        # Registra a similaridade simétrica para id2 -> id1
        sim_dict.setdefault(id2, []).append((id1, sim))

    # Extrai os IDs de todos os usuários da matriz pivô
    usuarios = matriz.index.tolist()
    # Se foi informado um usuário de referência específico
    if usuario_referencia:
        # Filtra a lista de usuários para considerar apenas o usuário desejado
        usuarios = [u for u in usuarios if u == usuario_referencia]

    # Inicializa a lista para armazenar todos os registros de recomendação a serem persistidos
    registros = []
    # Itera sobre cada usuário selecionado
    for user in usuarios:
        # Obtém a linha correspondente ao usuário atual na matriz pivô
        linha_usuario = matriz.loc[user]
        # Seleciona os IDs dos filmes que o usuário avaliou com nota maior que zero
        itens_avaliados = linha_usuario[linha_usuario > 0].index.tolist()
        # Se o usuário não tiver nenhum filme avaliado
        if not itens_avaliados:
            # Pula para o próximo usuário
            continue

        # Dicionário local para armazenar as notas previstas/pontuações acumuladas dos candidatos
        scores: dict[int, float] = {}
        # Itera sobre cada filme já avaliado pelo usuário
        for item_avaliado in itens_avaliados:
            # Obtém a nota dada pelo usuário a este filme
            rating_user = linha_usuario[item_avaliado]
            # Obtém a lista de filmes similares ao filme avaliado
            similares = sim_dict.get(item_avaliado, [])
            # Itera sobre cada filme similar e sua pontuação de similaridade
            for similar, sim in similares:
                # Se o filme similar ainda não foi avaliado pelo usuário
                if similar not in itens_avaliados:
                    # Acumula o score calculado como (nota_do_usuario * similaridade)
                    scores[similar] = scores.get(similar, 0.0) + (rating_user * sim)

        # Ordena a lista de filmes candidatos pelo score acumulado em ordem decrescente e seleciona os top_n
        filmes_recomendados = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        # Inicializa o ranking do usuário na posição 1
        rank = 1
        # Percorre os filmes recomendados e suas respectivas pontuações
        for movie_id, score in filmes_recomendados:
            # Adiciona o dicionário com os dados da recomendação à lista de registros
            registros.append(
                {
                    # Atribui o ID do usuário
                    "user_id": user,
                    # Atribui o ID do filme recomendado
                    "movie_id": movie_id,
                    # Atribui a pontuação final calculada
                    "score": float(score),
                    # Atribui a posição no ranking
                    "rank": rank,
                    # Atribui o nome do modelo 'collaborative_item_item'
                    "model_name": MODEL_NAME,
                    # Atribui a data/hora atual em UTC
                    "created_at": datetime.now(timezone.utc),
                }
            )
            # Incrementa a posição no ranking para a próxima recomendação
            rank += 1

    # Se foram gerados registros de recomendação
    if registros:
        # Converte a lista de registros para um DataFrame pandas
        df_rec = pd.DataFrame(registros)
        # Abre um bloco de transação com commit automático ao final da execução
        with engine.begin() as conn:
            # Remove todas as recomendações anteriores do modelo colaborativo
            conn.execute(
                text("DELETE FROM recommendations WHERE model_name = :modelo"),
                {"modelo": MODEL_NAME},
            )
            # Persiste os novos registros na tabela 'recommendations' no banco de dados
            df_rec.to_sql(
                "recommendations",
                conn,
                if_exists="append",
                index=False,
                method="multi",
            )
        # Grava mensagem de sucesso no logger detalhando a quantidade de usuários processados
        logger.info("Collaborative: recomendações geradas para %d usuários", len(usuarios))
    else:
        # Registra um aviso no log caso nenhuma recomendação tenha sido gerada
        logger.warning("Collaborative: nenhuma recomendação gerada")
