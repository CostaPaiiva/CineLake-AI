# Docstring do módulo indicando o modelo híbrido que combina abordagens baseadas em conteúdo e colaborativa item-item
"""Modelo híbrido que combina content-based e collaborative item-item."""

# Importa o módulo nativo de logging do Python para registro de diagnósticos e avisos
import logging

# Importa datetime e timezone para manipulação de datas/horas no formato UTC
from datetime import datetime, timezone

# Importa a biblioteca pandas para manipulação e estruturação de DataFrames
import pandas as pd

# Importa a função text do SQLAlchemy para construção de queries SQL puras parametrizadas
from sqlalchemy import text

# Importa a função get_engine da camada de acesso ao banco de dados do CineLake
from cinelake.db import get_engine

# Importa os nomes oficiais dos modelos base para consulta na tabela de recomendações
from cinelake.recommender.collaborative import MODEL_NAME as CF_MODEL
from cinelake.recommender.content_based import MODEL_NAME as CB_MODEL

# Inicializa o logger específico para este módulo usando __name__
logger = logging.getLogger(__name__)

# Define a constante global com o identificador deste modelo híbrido
MODEL_NAME = "hybrid"


# Função pública para gerar e salvar as recomendações híbridas no banco de dados
def gerar_recomendacoes_hibridas(
    top_n: int = 100,
    peso_content: float = 0.4,
    peso_collab: float = 0.6,
    usuario_referencia: int | None = None,
) -> None:
    # Docstring da função descrevendo a combinação de scores normalizados
    """
    Gera recomendações híbridas combinando scores normalizados dos dois modelos.

    Args:
        top_n: número máximo de recomendações por usuário.
        peso_content: peso para o modelo content-based.
        peso_collab: peso para o modelo collaborative.
        usuario_referencia: se fornecido, gera apenas para esse usuário.
    """
    # Obtém o objeto Engine de conexão com o banco de dados
    engine = get_engine()
    # Conecta ao banco de dados para buscar as recomendações salvas dos modelos base
    with engine.connect() as conn:
        # Busca as recomendações previamente salvas do modelo Content-Based
        cb = pd.read_sql(
            text("SELECT user_id, movie_id, score FROM recommendations WHERE model_name = :modelo"),
            conn,
            params={"modelo": CB_MODEL},
        )
        # Busca as recomendações previamente salvas do modelo Colaborativo
        cf = pd.read_sql(
            text("SELECT user_id, movie_id, score FROM recommendations WHERE model_name = :modelo"),
            conn,
            params={"modelo": CF_MODEL},
        )

    # Se um dos modelos base não possuir recomendações salvas no banco
    if cb.empty or cf.empty:
        # Grava erro no log informando a necessidade de executar os modelos base primeiro
        logger.error("Modelos base não têm recomendações. Execute-os antes.")
        # Encerra a execução da função
        return

    # Define a função interna auxiliar para normalização Min-Max dos scores por usuário
    def normalizar(df: pd.DataFrame) -> pd.DataFrame:
        # Cria uma cópia do DataFrame recebido para evitar mutação indesejada
        df = df.copy()
        # Normaliza a coluna score por usuário mapeando para o intervalo entre 0.0 e 1.0
        df["score_norm"] = df.groupby("user_id")["score"].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
        )
        # Retorna o DataFrame com a coluna 'score_norm' adicionada
        return df

    # Aplica a normalização dos scores no DataFrame de recomendações Content-Based
    cb_norm = normalizar(cb)
    # Aplica a normalização dos scores no DataFrame de recomendações Colaborativas
    cf_norm = normalizar(cf)

    # Executa a junção externa (outer join) dos dois dataframes chaveando por usuário e filme
    combinado = pd.merge(
        cb_norm[["user_id", "movie_id", "score_norm"]],
        cf_norm[["user_id", "movie_id", "score_norm"]],
        on=["user_id", "movie_id"],
        how="outer",
        suffixes=("_cb", "_cf"),
    )
    # Preenche com zero os valores nulos resultantes da junção externa
    combinado.fillna(0, inplace=True)

    # Calcula a pontuação final ponderada combinando os scores normalizados das duas abordagens
    combinado["score_final"] = (
        peso_content * combinado["score_norm_cb"] + peso_collab * combinado["score_norm_cf"]
    )

    # Ordena os registros por usuário (crescente) e por score_final (decrescente)
    combinado.sort_values(["user_id", "score_final"], ascending=[True, False], inplace=True)
    # Gera a posição de ranking (1, 2, 3...) para cada filme por usuário
    combinado["rank"] = combinado.groupby("user_id").cumcount() + 1

    # Filtra mantendo apenas os top_n filmes por usuário
    combinado = combinado[combinado["rank"] <= top_n]

    # Inicializa a lista de dicionários para os registros finais a serem gravados
    registros = []
    # Itera sobre cada linha do DataFrame combinado resultante
    for _, row in combinado.iterrows():
        # Adiciona o dicionário com os campos da recomendação híbrida à lista
        registros.append(
            {
                # Atribui o ID do usuário
                "user_id": int(row["user_id"]),
                # Atribui o ID do filme recomendado
                "movie_id": int(row["movie_id"]),
                # Atribui a pontuação final ponderada
                "score": float(row["score_final"]),
                # Atribui a posição no ranking
                "rank": int(row["rank"]),
                # Atribui o nome do modelo 'hybrid'
                "model_name": MODEL_NAME,
                # Atribui a data e hora em padrão UTC
                "created_at": datetime.now(timezone.utc),
            }
        )

    # Se foram gerados registros de recomendação híbrida
    if registros:
        # Converte a lista de dicionários para um DataFrame pandas
        df_rec = pd.DataFrame(registros)
        # Abre um bloco de transação com commit automático ao final da execução
        with engine.begin() as conn:
            # Remove as recomendações anteriores do modelo híbrido
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
        # Registra a mensagem de sucesso detalhando a quantidade de usuários contemplados
        logger.info("Hybrid: recomendações geradas para %d usuários", combinado["user_id"].nunique())
    else:
        # Registra um aviso no log caso nenhuma recomendação tenha sido gerada
        logger.warning("Hybrid: nenhuma recomendação gerada")
