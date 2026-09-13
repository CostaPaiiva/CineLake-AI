"""Comparação entre consulta com e sem índice em PostgreSQL."""

# Importa o módulo nativo de logging do Python para registro de logs e mensagens
import logging
# Importa o módulo nativo time para medição de tempo de execução das consultas
import time
# Importa Any do módulo typing para anotações de tipos genéricos
from typing import Any

# Importa a função text do SQLAlchemy para construção de queries SQL textuais seguras
from sqlalchemy import text

# Importa a função de fábrica para obter a Engine de conexão com o banco de dados
from cinelake.db import get_engine

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Função responsável por comparar a performance de consultas SQL com e sem índice no PostgreSQL
def benchmark_index_vs_no_index(tabela: str, coluna: str, valor: int, repeticoes: int = 5) -> dict[str, Any]:
    """
    Compara consulta com e sem índice.

    Assume que a tabela e a coluna existem e que o índice pode ser criado/removido.
    """
    # Registra no log o início do benchmark indicando a tabela e coluna avaliadas
    logger.info("Benchmark índice x sem índice em %s.%s", tabela, coluna)
    # Inicializa a engine do banco de dados configurada
    engine = get_engine()
    # Define um nome padronizado para o índice temporário do benchmark
    nome_indice = f"idx_bench_{tabela}_{coluna}"

    # Lista que armazenará os tempos de execução das consultas com índice
    tempos_com = []
    # Lista que armazenará os tempos de execução das consultas sem índice
    tempos_sem = []

    # Inicia uma transação gerenciada no banco de dados com commit/rollback automáticos
    with engine.begin() as conn:
        # Remove índice se existir
        # Garante que qualquer índice prévio com esse nome seja removido para iniciar o teste sem índice
        conn.execute(text(f"DROP INDEX IF EXISTS {nome_indice}"))

        # Sem índice
        # Executa a query repetidas vezes no cenário sem índice para calcular a média
        for _ in range(repeticoes):
            # Marca o timestamp de início da execução da query
            inicio = time.time()
            # Executa a consulta de contagem filtrando pela coluna especificada usando parâmetro bind
            conn.execute(
                # Monta a instrução SQL SELECT COUNT com bind parameter :valor
                text(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} = :valor"),
                # Passa o valor do filtro de forma segura
                {"valor": valor},
            ).scalar()
            # Calcula o tempo decorrido e adiciona na lista de medições sem índice
            tempos_sem.append(time.time() - inicio)

        # Cria índice
        # Cria o índice B-tree na tabela e coluna especificadas para o teste com índice
        conn.execute(text(f"CREATE INDEX {nome_indice} ON {tabela}({coluna})"))

        # Com índice
        # Executa a query repetidas vezes no cenário com índice criado
        for _ in range(repeticoes):
            # Marca o timestamp de início da execução da query
            inicio = time.time()
            # Executa a mesma consulta de contagem agora se beneficiando do índice
            conn.execute(
                # Monta a instrução SQL SELECT COUNT com bind parameter :valor
                text(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} = :valor"),
                # Passa o valor do filtro de forma segura
                {"valor": valor},
            ).scalar()
            # Calcula o tempo decorrido e adiciona na lista de medições com índice
            tempos_com.append(time.time() - inicio)

        # Remove índice ao final
        # Limpa o banco de dados removendo o índice criado após a conclusão das medições
        conn.execute(text(f"DROP INDEX IF EXISTS {nome_indice}"))

    # Retorna o dicionário consolidado contendo os dados e métricas do benchmark
    return {
        # Identificador do tipo de benchmark
        "benchmark": "index_vs_no_index",
        # Nome da tabela testada
        "tabela": tabela,
        # Nome da coluna testada
        "coluna": coluna,
        # Tempo médio de execução em segundos das consultas sem índice
        "tempo_medio_sem_indice_s": round(sum(tempos_sem) / len(tempos_sem), 5),
        # Tempo médio de execução em segundos das consultas com índice
        "tempo_medio_com_indice_s": round(sum(tempos_com) / len(tempos_com), 5),
        # Porcentagem de ganho de desempenho obtida com o índice
        "ganho_pct": round(
            # Fórmula de cálculo do percentual de ganho de tempo
            (1 - sum(tempos_com) / sum(tempos_sem)) * 100, 2
        ) if sum(tempos_sem) > 0 else 0,
    }
