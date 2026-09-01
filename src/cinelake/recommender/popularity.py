# Docstring do módulo indicando que este arquivo trata do modelo baseline por popularidade
"""Modelo de recomendação baseline por popularidade."""

# Importa o módulo nativo de logging do Python
import logging
# Importa datetime e timezone do módulo datetime para manipulação de datas com fuso horário
from datetime import datetime, timezone

# Importa a biblioteca pandas para manipulação e análise de dados em DataFrames
import pandas as pd
# Importa o construtor text do SQLAlchemy para execução de SQL nativo com segurança
from sqlalchemy import text

# Importa a função get_engine do módulo cinelake.db para obter conexão com o banco de dados
from cinelake.db import get_engine

# Instancia o logger específico para este módulo usando o nome do próprio módulo (__name__)
logger = logging.getLogger(__name__)


# Define a função para calcular a pontuação de popularidade dos filmes
def calcular_popularidade(min_votos: int = 50) -> pd.DataFrame:
    # Docstring da função descrevendo a fórmula de popularidade e seus parâmetros
    """
    Calcula score de popularidade ponderada para cada filme.

    Fórmula: (v/(v+m))*R + (m/(v+m))*C

    Args:
        min_votos: mínimo de votos para considerar o filme (m).

    Returns:
        DataFrame com colunas: movie_id, score_popularidade, total_votos, media_nota.
    """
    # Obtém o objeto Engine do SQLAlchemy configurado no projeto
    engine = get_engine()
    # Abre um bloco de conexão com o banco de dados que será fechado automaticamente
    with engine.connect() as conn:
        # Executa a consulta SQL para obter a média global de todas as avaliações (C)
        media_global = conn.execute(
            # Consulta SQL pura para calcular a média da coluna rating da tabela ratings
            text("SELECT AVG(rating) FROM ratings")
        ).scalar()  # Extrai o valor escalar retornado pela consulta
        # Converte o valor retornado para float se existir, caso contrário assume 0.0
        media_global = float(media_global) if media_global else 0.0

        # Lê do banco de dados agregando contagem total e média de notas por filme (R e v)
        df = pd.read_sql(
            # Consulta SQL agregando por movie_id
            text("""
                SELECT movie_id, COUNT(*) AS total_votos, AVG(rating) AS media_nota
                FROM ratings
                GROUP BY movie_id
            """),
            # Passa a conexão com o banco de dados para o pandas
            conn,
        )

    # Verifica se o DataFrame retornado está vazio
    if df.empty:
        # Retorna o DataFrame vazio imediatamente se não houver registros
        return df

    # Converte a coluna total_votos para o tipo float (v)
    v = df["total_votos"].astype(float)
    # Converte a coluna media_nota para o tipo float (R)
    R = df["media_nota"].astype(float)
    # Converte o parâmetro min_votos para float (m)
    m = float(min_votos)
    # Atribui a média global a uma variável local (C)
    C = media_global

    # Aplica a fórmula de pontuação ponderada do IMDB em cada linha
    df["score_popularidade"] = (v / (v + m)) * R + (m / (v + m)) * C
    # Ordena o DataFrame de forma decrescente pelo score de popularidade calculado
    df = df.sort_values("score_popularidade", ascending=False)

    # Retorna o DataFrame resultante final ordenado
    return df


# Define a função para gerar e persistir recomendações baseadas em popularidade
def gerar_recomendacoes_populares(top_n: int = 100, modelo: str = "popularity_baseline") -> None:
    # Docstring da função descrevendo a geração em lote de recomendações
    """
    Gera recomendações populares para todos os usuários (não personalizado).

    Args:
        top_n: número de recomendações por usuário.
        modelo: nome do modelo para gravação.
    """
    # Obtém o Engine de banco de dados
    engine = get_engine()
    # Executa a função de cálculo de popularidade para obter o DataFrame ordenado
    df_populares = calcular_popularidade()

    # Caso não existam dados calculados de popularidade
    if df_populares.empty:
        # Registra um aviso no log informando a ausência de dados
        logger.warning("Sem dados para gerar recomendações populares")
        # Interrompe a execução da função
        return

    # Extrai os IDs dos top_n filmes com maior pontuação de popularidade como lista
    top_filmes = df_populares.head(top_n)["movie_id"].tolist()

    # Abre conexão com o banco de dados para buscar a lista de usuários
    with engine.connect() as conn:
        # Executa consulta SQL e extrai lista contendo o ID de todos os usuários únicos
        usuarios = [row[0] for row in conn.execute(text("SELECT DISTINCT user_id FROM ratings")).fetchall()]

    # Caso não exista nenhum usuário cadastrado
    if not usuarios:
        # Registra um aviso no log
        logger.warning("Nenhum usuário encontrado")
        # Interrompe a execução
        return

    # Inicializa uma lista vazia para armazenar os dicionários de cada recomendação
    registros = []
    # Inicializa a variável de controle de posição (rank) iniciando em 1
    rank = 1
    # Percorre cada usuário retornado do banco
    for user in usuarios:
        # Percorre a lista dos filmes mais populares
        for movie_id in top_filmes:
            # Adiciona o dicionário com os campos da recomendação à lista
            registros.append(
                {
                    # Atribui o ID do usuário atual
                    "user_id": user,
                    # Atribui o ID do filme atual
                    "movie_id": movie_id,
                    # Atribui score fixo igual a 1.0 (não personalizado)
                    "score": 1.0,
                    # Atribui a posição no ranking
                    "rank": rank,
                    # Atribui o identificador do modelo utilizado
                    "model_name": modelo,
                    # Atribui a data e hora atual em UTC no formato timezone aware
                    "created_at": datetime.now(timezone.utc),
                }
            )
            # Incrementa o rank para a próxima posição do mesmo usuário
            rank += 1
        # Reinicia o rank para 1 antes de iterar sobre o próximo usuário
        rank = 1

    # Converte a lista de dicionários de registros em um DataFrame do pandas
    df_rec = pd.DataFrame(registros)

    # Abre um bloco de transação com engine.begin() para garantir commit automático ao final
    with engine.begin() as conn:
        # Remove do banco todas as recomendações salvas anteriormente para este modelo específico
        conn.execute(
            # Comando SQL de remoção parametrizado
            text("DELETE FROM recommendations WHERE model_name = :modelo"),
            # Passa o nome do modelo como parâmetro do SQL
            {"modelo": modelo},
        )
        # Escreve o DataFrame contendo as novas recomendações na tabela 'recommendations'
        df_rec.to_sql(
            # Nome da tabela de destino no banco de dados
            "recommendations",
            # Objeto de conexão ativo da transação
            conn,
            # Se a tabela já existir, adiciona as novas linhas ao final dela
            if_exists="append",
            # Não salva o índice do DataFrame como coluna no banco
            index=False,
            # Utiliza inserções em múltiplos valores por instrução SQL para maior performance
            method="multi",
        )

    # Registra no log a conclusão bem sucedida do processo informando a quantidade de usuários
    logger.info("Recomendações populares geradas para %d usuários", len(usuarios))
