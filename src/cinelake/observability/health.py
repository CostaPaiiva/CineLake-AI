"""Funções para coletar métricas de saúde e métricas operacionais da plataforma."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)


def verificar_conexao_postgres() -> bool:
    """Verifica se o banco de dados PostgreSQL está ativo e respondendo às requisições.

    Returns:
        bool: True se a conexão for bem-sucedida, False caso contrário.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Falha na conexão com PostgreSQL: %s", exc)
        return False


def obter_contagens_tabelas() -> dict[str, int]:
    """Retorna a contagem de registros/linhas das principais tabelas do banco de dados.

    Returns:
        dict[str, int]: Dicionário mapeando o nome de cada tabela à quantidade de registros.
    """
    engine = get_engine()
    tabelas = ["movies", "ratings", "tags", "links", "dim_movie", "fact_rating"]
    contagens = {}
    with engine.connect() as conn:
        for tabela in tabelas:
            try:
                resultado = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
                val = resultado.scalar()
                contagens[tabela] = int(val) if val is not None else -1
            except Exception as exc:
                logger.warning("Erro ao contar registros da tabela %s: %s", tabela, exc)
                contagens[tabela] = -1
    return contagens


def obter_ultimas_execucoes() -> dict[str, dict[str, Any]]:
    """Consulta a tabela `ingestion_batch` e retorna a última execução bem-sucedida de cada fonte de dados.

    Returns:
        dict[str, dict[str, Any]]: Dicionário com timestamp ISO e frescor em minutos de cada fonte.
    """
    engine = get_engine()
    query = text("""
        SELECT source, MAX(finished_at) AS ultima_execucao
        FROM ingestion_batch
        WHERE status = 'success'
        GROUP BY source
    """)
    resultados: dict[str, dict[str, Any]] = {}
    with engine.connect() as conn:
        linhas = conn.execute(query).fetchall()
        for linha in linhas:
            source = linha[0]
            ultima = linha[1]
            resultados[source] = {
                "ultima_execucao": ultima.isoformat() if ultima else None,
                "freshness_minutos": _calcular_freshness_minutos(ultima),
            }
    return resultados


def _calcular_freshness_minutos(timestamp: datetime | None) -> float | None:
    """Calcula a diferença em minutos entre o timestamp fornecido e o horário atual (UTC).

    Args:
        timestamp: Timestamp da última execução.

    Returns:
        float | None: Intervalo em minutos ou None caso o timestamp seja nulo.
    """
    if timestamp is None:
        return None
    agora = datetime.now(timezone.utc)
    delta = agora - timestamp
    return round(delta.total_seconds() / 60, 2)


def coletar_status_geral() -> dict[str, Any]:
    """Coleta e consolida o status geral de saúde e métricas operacionais da plataforma CineLake AI.

    Returns:
        dict[str, Any]: Dicionário contendo status, timestamp, contagens e frescor das fontes.
    """
    conexao_ok = verificar_conexao_postgres()
    if not conexao_ok:
        return {"status": "down", "erro": "PostgreSQL inacessível"}

    contagens = obter_contagens_tabelas()
    ultimas = obter_ultimas_execucoes()

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contagens": contagens,
        "fontes": ultimas,
    }
