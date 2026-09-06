# =====================================================================
# Script Python para avaliação e população da tabela model_metrics
# =====================================================================

import logging  # Módulo nativo para log de mensagens e diagnósticos
import pandas as pd  # Biblioteca para manipulação de dados em formato DataFrame
from cinelake.db import get_engine  # Função de conexão com o banco de dados PostgreSQL
from cinelake.recommender.evaluate_models import avaliar_modelos  # Função unificada de avaliação

# Configuração básica do logger para exibição de mensagens de nível INFO no console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)  # Instancia o logger do módulo corrente


def main() -> None:  # Função principal de execução do script
    logger.info("Iniciando a avaliação de todos os modelos de recomendação...")  # Log de início

    engine = get_engine()  # Obtém o Engine SQLAlchemy conectado ao banco cinelake
    resultados = avaliar_modelos(top_k=10)  # Executa a avaliação unificada para top_k=10

    dados = []  # Lista para acumular os dicionários com as métricas consolidadas
    for model_name, metricas in resultados.items():  # Percorre cada modelo e seu dicionário de métricas
        if isinstance(metricas, dict) and "error" not in metricas:  # Filtra resultados válidos sem erro
            dados.append(  # Adiciona as métricas do modelo à lista dados
                {
                    "model_name": model_name,  # Nome do modelo de recomendação
                    "precision_medio": metricas.get("precision_medio", metricas.get("precision", 0.0)),  # Precisão média
                    "recall_medio": metricas.get("recall_medio", metricas.get("recall", 0.0)),  # Recall médio
                    "hit_rate": metricas.get("hit_rate", 0.0),  # Hit Rate
                }
            )

    if dados:  # Se houver dados válidos coletados
        df = pd.DataFrame(dados)  # Converte a lista em DataFrame pandas
        df.to_sql("model_metrics", engine, if_exists="replace", index=False)  # Salva no banco na tabela model_metrics
        logger.info("Tabela 'model_metrics' populada com sucesso no PostgreSQL com %d modelos!", len(dados))  # Sucesso
    else:  # Caso nenhum modelo tenha retornado métricas válidas
        logger.warning("Nenhuma métrica foi gerada para popular a tabela 'model_metrics'.")  # Aviso


if __name__ == "__main__":  # Garante que a função main seja executada ao chamar o script diretamente
    main()  # Executa a função main
