"""Executa todos os benchmarks e salva resultados."""

# Importa o módulo json para persistir os resultados coletados em formato estruturado
import json
# Importa o módulo nativo de logging do Python para registro de mensagens
import logging
# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos e diretórios
from pathlib import Path

# Importa a função de execução do benchmark de CSV versus Parquet
from cinelake.benchmarks.csv_vs_parquet import benchmark_csv_vs_parquet
# Importa a função de execução do benchmark de consulta com e sem índice no banco relacional
from cinelake.benchmarks.index_vs_no_index import benchmark_index_vs_no_index
# Importa a função de execução do benchmark de latência com e sem cache Redis
from cinelake.benchmarks.redis_vs_no_redis import benchmark_redis_vs_no_redis
# Importa a função de execução do benchmark de ingestão Full versus Incremental
from cinelake.benchmarks.incremental_vs_full import benchmark_incremental_vs_full

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Função principal orquestradora que executa todos os benchmarks do projeto
def executar_todos_benchmarks() -> list[dict]:
    """Executa todos os benchmarks configurados."""
    # Lista para armazenar todos os dicionários de resultados de cada benchmark executado
    resultados = []

    # 1. CSV x Parquet
    # Bloco protegido para execução do benchmark de formatos de arquivo
    try:
        # Define o caminho do arquivo de origem CSV do MovieLens
        caminho_csv = Path("data/raw/movielens/ml-latest-small/ratings.csv")
        # Define o caminho de destino onde o arquivo Parquet gerado será salvo
        caminho_parquet = Path("data/benchmarks/ratings.parquet")
        # Cria a pasta data/benchmarks caso ainda não exista no sistema
        caminho_parquet.parent.mkdir(parents=True, exist_ok=True)
        # Verifica se o arquivo CSV de origem existe antes de iniciar o benchmark
        if caminho_csv.exists():
            # Executa o benchmark de CSV vs Parquet e adiciona o resultado na lista
            resultados.append(benchmark_csv_vs_parquet(caminho_csv, caminho_parquet))
        else:
            # Emite aviso no log caso o arquivo de dados do MovieLens não seja encontrado
            logger.warning("CSV não encontrado: %s", caminho_csv)
    # Captura e trata exceções sem interromper a execução dos demais benchmarks
    except Exception as exc:
        # Registra erro no log com os detalhes da falha no benchmark de CSV x Parquet
        logger.error("Falha no benchmark CSV x Parquet: %s", exc)

    # 2. Índice x Sem índice
    # Bloco protegido para execução do benchmark de índices no banco de dados
    try:
        # Executa o teste comparativo de consulta com e sem índice na tabela ratings
        resultados.append(benchmark_index_vs_no_index("ratings", "movie_id", 1))
    # Captura e trata exceções sem interromper a execução dos demais benchmarks
    except Exception as exc:
        # Registra erro no log com os detalhes da falha no benchmark de índice
        logger.error("Falha no benchmark índice: %s", exc)

    # 3. Redis x Sem Redis
    # Bloco protegido para execução do benchmark de caching com Redis
    try:
        # Executa o teste comparativo de tempo de resposta com e sem cache Redis para o filme com ID 1
        resultados.append(benchmark_redis_vs_no_redis(1))
    # Captura e trata exceções sem interromper a execução dos demais benchmarks
    except Exception as exc:
        # Registra erro no log com os detalhes da falha no benchmark do Redis
        logger.error("Falha no benchmark Redis: %s", exc)

    # 4. Full x Incremental
    # Bloco protegido para execução do benchmark de carga Full vs Incremental
    try:
        # Define o caminho do arquivo CSV do MovieLens utilizado para o teste de carga
        caminho_csv = Path("data/raw/movielens/ml-latest-small/ratings.csv")
        # Verifica se o arquivo CSV existe no sistema
        if caminho_csv.exists():
            # Executa o benchmark de ingestão incremental vs full e adiciona na lista de resultados
            resultados.append(benchmark_incremental_vs_full(caminho_csv))
    # Captura e trata exceções sem interromper a execução dos demais benchmarks
    except Exception as exc:
        # Registra erro no log com os detalhes da falha no benchmark incremental
        logger.error("Falha no benchmark incremental: %s", exc)

    # Salva resultados
    # Define o caminho do arquivo JSON onde todos os resultados serão persistidos
    saida = Path("docs/benchmarks/resultados.json")
    # Cria os diretórios da pasta docs/benchmarks caso ainda não existam
    saida.parent.mkdir(parents=True, exist_ok=True)
    # Abre o arquivo de saída em modo de escrita com codificação UTF-8
    with saida.open("w", encoding="utf-8") as f:
        # Serializa e salva a lista de resultados em JSON com indentação de 2 espaços
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    # Registra no MLflow
    # Bloco protegido para registrar as métricas apuradas no servidor MLflow
    try:
        # Importa a função utilitária para envio de parâmetros e métricas ao MLflow
        from cinelake.mlops.tracking import log_parametros_e_metricas
        # Itera sobre cada dicionário de resultado obtido nos benchmarks
        for r in resultados:
            # Filtra apenas os campos numéricos (inteiros ou floats) que representam métricas
            metricas = {
                # Chave da métrica
                k: v
                # Itera sobre os pares chave-valor do dicionário de resultados
                for k, v in r.items()
                # Mantém apenas valores numéricos excluindo o campo identificador de nome
                if isinstance(v, (int, float)) and k != "benchmark"
            }
            # Registra no experimento 'benchmarks' do MLflow os parâmetros e métricas apurados
            log_parametros_e_metricas(
                # Nome do experimento no MLflow
                experimento_nome="benchmarks",
                # Dicionário contendo os parâmetros de identificação do benchmark
                parametros={"benchmark": r.get("benchmark", "unknown")},
                # Dicionário contendo todas as métricas numéricas apuradas
                metricas=metricas,
            )
    # Captura e trata exceções caso o servidor MLflow não esteja disponível
    except Exception as exc:
        # Registra aviso no log informando a impossibilidade de envio para o MLflow
        logger.warning("Falha ao registrar benchmarks no MLflow: %s", exc)

    # Retorna a lista completa com todos os resultados obtidos
    return resultados
