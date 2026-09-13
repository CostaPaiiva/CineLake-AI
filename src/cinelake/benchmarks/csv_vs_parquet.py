"""Comparação entre CSV e Parquet para leitura de dados."""

# Importa o módulo nativo de logging do Python para registro de mensagens
import logging
# Importa o módulo nativo de tempo para medição do tempo de execução
import time
# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos no sistema de arquivos
from pathlib import Path
# Importa Any do módulo typing para anotações de tipos genéricos
from typing import Any

# Importa a biblioteca pandas para manipulação e leitura de dados em estruturas DataFrame
import pandas as pd
# Importa o submódulo de parquet do PyArrow para leitura eficiente de arquivos em formato Parquet
import pyarrow.parquet as pq

# Obtém a instância do logger configurada para o módulo atual (__name__)
logger = logging.getLogger(__name__)


# Função principal que realiza o teste comparativo de desempenho entre CSV e Parquet
def benchmark_csv_vs_parquet(caminho_csv: Path, caminho_parquet: Path, repeticoes: int = 3) -> dict[str, Any]:
    """
    Compara tempo de leitura e tamanho em disco entre CSV e Parquet.

    Retorna dicionário com métricas.
    """
    # Registra no log o início da execução do benchmark
    logger.info("Benchmark CSV x Parquet")

    # Garante que o Parquet existe
    # Verifica se o arquivo Parquet de destino já existe no disco
    if not caminho_parquet.exists():
        # Registra no log que a conversão do CSV para Parquet será iniciada
        logger.info("Convertendo CSV para Parquet...")
        # Lê o arquivo CSV completo para um DataFrame do pandas
        df = pd.read_csv(caminho_csv)
        # Salva o DataFrame no formato Parquet comprimido sem incluir o índice de linhas
        df.to_parquet(caminho_parquet, index=False)

    # Calcula o tamanho do arquivo CSV em Megabytes (MB)
    tamanho_csv_mb = caminho_csv.stat().st_size / (1024 * 1024)
    # Calcula o tamanho do arquivo Parquet em Megabytes (MB)
    tamanho_parquet_mb = caminho_parquet.stat().st_size / (1024 * 1024)

    # Lista para armazenar o tempo gasto em cada repetição da leitura do CSV
    tempos_csv = []
    # Lista para armazenar o tempo gasto em cada repetição da leitura do Parquet
    tempos_parquet = []

    # Loop para executar a medição repetidas vezes e obter uma média confiável
    for i in range(repeticoes):
        # CSV
        # Marca o timestamp de início da leitura do arquivo CSV
        inicio = time.time()
        # Executa a leitura do CSV descartando o retorno na variável '
        _ = pd.read_csv(caminho_csv)
        # Calcula a diferença de tempo e adiciona o resultado à lista de tempos do CSV
        tempos_csv.append(time.time() - inicio)

        # Parquet
        # Marca o timestamp de início da leitura do arquivo Parquet
        inicio = time.time()
        # Executa a leitura da tabela Parquet via PyArrow e converte para DataFrame do pandas
        _ = pq.read_table(caminho_parquet).to_pandas()
        # Calcula a diferença de tempo e adiciona o resultado à lista de tempos do Parquet
        tempos_parquet.append(time.time() - inicio)

        # Registra no log os tempos medidos para a repetição atual
        logger.info("Repetição %d: CSV=%.2fs Parquet=%.2fs", i + 1, tempos_csv[-1], tempos_parquet[-1])

    # Monta o dicionário com todas as métricas consolidadas do benchmark
    resultado = {
        # Nome identificador do benchmark executado
        "benchmark": "csv_vs_parquet",
        # Tamanho do arquivo CSV formatado em MB com 2 casas decimais
        "tamanho_csv_mb": round(tamanho_csv_mb, 2),
        # Tamanho do arquivo Parquet formatado em MB com 2 casas decimais
        "tamanho_parquet_mb": round(tamanho_parquet_mb, 2),
        # Tempo médio de leitura do CSV em segundos formatado com 3 casas decimais
        "tempo_medio_csv_s": round(sum(tempos_csv) / len(tempos_csv), 3),
        # Tempo médio de leitura do Parquet em segundos formatado com 3 casas decimais
        "tempo_medio_parquet_s": round(sum(tempos_parquet) / len(tempos_parquet), 3),
        # Porcentagem de redução do tamanho do arquivo obtida ao utilizar Parquet em relação ao CSV
        "reducao_tamanho_pct": round((1 - tamanho_parquet_mb / tamanho_csv_mb) * 100, 2),
        # Porcentagem do ganho de velocidade/desempenho na leitura do Parquet em relação ao CSV
        "ganho_velocidade_pct": round(
            (1 - (sum(tempos_parquet) / sum(tempos_csv))) * 100, 2
        ),
    }
    # Retorna o dicionário consolidado com os resultados do benchmark
    return resultado
