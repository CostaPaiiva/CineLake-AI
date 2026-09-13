"""Comparação entre ingestão full e incremental (MovieLens)."""

# Importa o módulo nativo de logging do Python para emissão de logs
import logging
# Importa o módulo nativo time para medição de tempo de execução
import time
# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos de arquivos
from pathlib import Path

# Importa a biblioteca pandas para manipulação eficiente de dados tabulares
import pandas as pd
# Importa a função text do SQLAlchemy para construção de queries SQL
from sqlalchemy import text

# Importa a função de conexão para obter a Engine do banco de dados
from cinelake.db import get_engine

# Obtém a instância do logger configurada para o módulo atual
logger = logging.getLogger(__name__)


# Função principal que realiza o benchmark comparativo entre carga full e carga incremental
def benchmark_incremental_vs_full(caminho_csv: Path, repeticoes: int = 3) -> dict:
    """Compara ingestão full (recarrega tudo) versus incremental (somente novos)."""
    # Registra no log o início da execução do benchmark
    logger.info("Benchmark ingestão full x incremental")

    # Lê o arquivo CSV com os dados de avaliações (ratings) para um DataFrame pandas
    df = pd.read_csv(caminho_csv)
    # Valida se o DataFrame está vazio antes de prosseguir com os cálculos
    if df.empty:
        # Retorna dicionário informando o erro de arquivo vazio
        return {"benchmark": "incremental_vs_full", "erro": "CSV vazio"}

    # Simula watermark = mediana dos timestamps
    # Define a marca d'água (watermark) simulada como sendo a mediana (percentil 50%) da coluna de timestamp 'ts'
    watermark = int(df["ts"].quantile(0.5))

    # Lista para armazenar os tempos de execução da abordagem full
    tempos_full = []
    # Lista para armazenar os tempos de execução da abordagem incremental
    tempos_incr = []

    # Inicializa a Engine de conexão com o banco de dados
    engine = get_engine()

    # Loop para executar a medição repetidas vezes e obter uma média estatística confiável
    for _ in range(repeticoes):
        # Full (apenas contagem de linhas, para não duplicar dados)
        # Marca o timestamp de início da consulta full no banco de dados
        inicio = time.time()
        # Abre conexão com o banco de dados
        with engine.connect() as conn:
            # Executa a contagem total de todas as linhas da tabela de ratings
            conn.execute(text("SELECT COUNT(*) FROM ratings")).scalar()
        # Calcula a duração da consulta full e adiciona na lista de medições
        tempos_full.append(time.time() - inicio)

        # Incremental (apenas novas linhas)
        # Marca o timestamp de início da filtragem incremental
        inicio = time.time()
        # Filtra apenas os registros cujo timestamp é mais recente que a marca d'água (watermark)
        novos = df[df["ts"] > watermark]
        # Executa a contagem apenas dos novos registros filtrados
        _ = len(novos)
        # Calcula a duração do processamento incremental e adiciona na lista de medições
        tempos_incr.append(time.time() - inicio)

    # Retorna o dicionário consolidado contendo todas as métricas apuradas
    return {
        # Nome identificador do benchmark executado
        "benchmark": "incremental_vs_full",
        # Tempo médio em segundos do processamento full (com 5 casas decimais)
        "tempo_medio_full_s": round(sum(tempos_full) / len(tempos_full), 5),
        # Tempo médio em segundos do processamento incremental (com 5 casas decimais)
        "tempo_medio_incremental_s": round(sum(tempos_incr) / len(tempos_incr), 5),
        # Quantidade total de linhas contidas no dataset completo
        "linhas_total": len(df),
        # Quantidade de novas linhas processadas incrementalmente acima do watermark
        "linhas_incrementais": len(novos),
        # Porcentagem de ganho de desempenho obtido com a estratégia incremental
        "ganho_pct": round(
            # Fórmula de cálculo do ganho percentual de tempo
            (1 - sum(tempos_incr) / sum(tempos_full)) * 100, 2
        ) if sum(tempos_full) > 0 else 0,
    }
