"""Benchmark de partition pruning em Parquet."""

# Importa o módulo nativo de logging do Python para registro de mensagens
import logging

# Importa o módulo nativo time para medição precisa de tempo de execução
import time

# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos de arquivos e diretórios
from pathlib import Path

# Importa Any do módulo typing para anotações de tipos genéricos
from typing import Any

# Importa o módulo dataset do PyArrow para leitura particionada e aplicação de filtros em datasets
import pyarrow.dataset as ds

# Importa o módulo parquet do PyArrow para operações de leitura direta de arquivos Parquet
import pyarrow.parquet as pq

# Obtém a instância do logger configurada para o módulo atual
logger = logging.getLogger(__name__)


# Função principal responsável por executar o benchmark comparativo de partition pruning
def benchmark_partition_pruning(
    diretorio_partitioned: Path, filtro: dict[str, Any], repeticoes: int = 3
) -> dict[str, Any]:
    """
    Compara leitura completa versus leitura com partition pruning.

    Assume que os arquivos estão em diretório particionado por year/month/day.
    """
    # Registra no log o início da execução do benchmark informando o diretório avaliado
    logger.info("Benchmark partition pruning em %s", diretorio_partitioned)

    # Lista para armazenar as medições de tempo da leitura completa de todas as partições
    tempos_full = []
    # Lista para armazenar as medições de tempo da leitura com partition pruning (filtro de partição)
    tempos_pruned = []

    # Executa o loop com a quantidade de repetições configuradas para calcular as médias
    for _ in range(repeticoes):
        # Leitura completa
        # Marca o timestamp de início da leitura de todo o diretório particionado sem filtros
        inicio = time.time()
        # Lê todas as partições Parquet existentes e converte a tabela completa para DataFrame pandas
        _ = pq.read_table(diretorio_partitioned).to_pandas()
        # Calcula o tempo total decorrido na leitura completa e adiciona à lista de tempos full
        tempos_full.append(time.time() - inicio)

        # Leitura com filtro (partition pruning)
        # Marca o timestamp de início da leitura utilizando o mecanismo de partition pruning
        inicio = time.time()
        # Mapeia a estrutura particionada do diretório utilizando o padrão de particionamento Hive
        dataset = ds.dataset(diretorio_partitioned, format="parquet", partitioning="hive")
        # Lê apenas os arquivos da partição correspondente ao filtro especificado e converte para DataFrame
        _ = dataset.to_table(filter=ds.field("year") == filtro["year"]).to_pandas()
        # Calcula o tempo total decorrido na leitura filtrada e adiciona à lista de tempos pruned
        tempos_pruned.append(time.time() - inicio)

    # Retorna o dicionário consolidado contendo todas as métricas apuradas
    return {
        # Nome identificador do benchmark executado
        "benchmark": "partition_pruning",
        # Tempo médio em segundos para ler todo o dataset particionado (com 3 casas decimais)
        "tempo_medio_full_s": round(sum(tempos_full) / len(tempos_full), 3),
        # Tempo médio em segundos para ler apenas as partições filtradas (com 3 casas decimais)
        "tempo_medio_pruned_s": round(sum(tempos_pruned) / len(tempos_pruned), 3),
        # Porcentagem de ganho de performance e redução no tempo de leitura
        "ganho_pct": round(
            # Fórmula matemática de cálculo do ganho percentual de tempo
            (1 - sum(tempos_pruned) / sum(tempos_full)) * 100,
            2,
        )
        if sum(tempos_full) > 0
        else 0,
    }
