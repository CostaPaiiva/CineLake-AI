"""Coletor de documentos para RAG.

Varre documentação, modelos dbt, contratos e metadados do banco,
normaliza e salva em data/rag/documents/.
"""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text

from cinelake.db import get_engine
from cinelake.rag.normalizer import criar_documento, salvar_documentos

logger = logging.getLogger(__name__)


def coletar_adrs(diretorio_docs: Path) -> list[dict[str, Any]]:
    """Coleta todos os registros de decisão de arquitetura (ADRs) em docs/adr/*.md.

    Args:
        diretorio_docs: Caminho base da pasta de documentação (docs/).

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados do tipo ADR.
    """
    documentos = []
    diretorio_adr = diretorio_docs / "adr"
    if diretorio_adr.exists():
        for arquivo in diretorio_adr.glob("*.md"):
            conteudo = arquivo.read_text(encoding="utf-8")
            documentos.append(
                criar_documento(
                    titulo=f"ADR: {arquivo.stem}",
                    conteudo=conteudo,
                    fonte="adr",
                    metadados={"arquivo": str(arquivo)},
                )
            )
    return documentos


def coletar_runbooks(diretorio_docs: Path) -> list[dict[str, Any]]:
    """Coleta os runbooks operacionais localizados em docs/runbooks/*.md.

    Args:
        diretorio_docs: Caminho base da pasta de documentação (docs/).

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados contendo procedimentos operacionais.
    """
    documentos = []
    diretorio_run = diretorio_docs / "runbooks"
    if diretorio_run.exists():
        for arquivo in diretorio_run.glob("*.md"):
            conteudo = arquivo.read_text(encoding="utf-8")
            documentos.append(
                criar_documento(
                    titulo=f"Runbook: {arquivo.stem}",
                    conteudo=conteudo,
                    fonte="runbook",
                    metadados={"arquivo": str(arquivo)},
                )
            )
    return documentos


def coletar_modelos_dbt(diretorio_dbt: Path) -> list[dict[str, Any]]:
    """Coleta as definições de modelos dbt (consultas SQL e arquivos de esquema YAML).

    Args:
        diretorio_dbt: Caminho base do projeto dbt (dbt_project/).

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados dos modelos e schemas dbt.
    """
    documentos = []
    diretorio_modelos = diretorio_dbt / "models"
    if diretorio_modelos.exists():
        for arquivo in diretorio_modelos.rglob("*.sql"):
            conteudo = arquivo.read_text(encoding="utf-8")
            documentos.append(
                criar_documento(
                    titulo=f"Modelo dbt: {arquivo.stem}",
                    conteudo=conteudo,
                    fonte="dbt_model",
                    metadados={"arquivo": str(arquivo)},
                )
            )
        for arquivo in diretorio_modelos.rglob("*.yml"):
            conteudo = arquivo.read_text(encoding="utf-8")
            documentos.append(
                criar_documento(
                    titulo=f"Schema dbt: {arquivo.stem}",
                    conteudo=conteudo,
                    fonte="dbt_schema",
                    metadados={"arquivo": str(arquivo)},
                )
            )
    return documentos


def coletar_contratos(diretorio_contratos: Path) -> list[dict[str, Any]]:
    """Coleta as regras e especificações dos contratos de dados definidos no código Python.

    Args:
        diretorio_contratos: Caminho da pasta de contratos de qualidade de dados.

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados de contratos de dados.
    """
    documentos = []
    if diretorio_contratos.exists():
        for arquivo in diretorio_contratos.glob("*.py"):
            conteudo = arquivo.read_text(encoding="utf-8")
            documentos.append(
                criar_documento(
                    titulo=f"Contrato de dados: {arquivo.stem}",
                    conteudo=conteudo,
                    fonte="data_contract",
                    metadados={"arquivo": str(arquivo)},
                )
            )
    return documentos


def coletar_schema_tabelas() -> list[dict[str, Any]]:
    """Coleta em tempo de execução os esquemas e definições de colunas das tabelas do PostgreSQL.

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados contendo a estrutura de cada tabela.
    """
    engine = get_engine()
    documentos = []
    with engine.connect() as conn:
        # Lista tabelas do schema public (apenas as principais)
        resultado = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )
        tabelas = [row[0] for row in resultado]
        for tabela in tabelas:
            colunas = conn.execute(
                text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :tabela
                    ORDER BY ordinal_position
                """),
                {"tabela": tabela},
            ).fetchall()
            descricao = "\n".join(
                [f"{col[0]} ({col[1]}) nullable={col[2]}" for col in colunas]
            )
            documentos.append(
                criar_documento(
                    titulo=f"Schema da tabela: {tabela}",
                    conteudo=f"Tabela: {tabela}\n{descricao}",
                    fonte="table_schema",
                    metadados={"tabela": tabela},
                )
            )
    return documentos


def coletar_ultimas_execucoes() -> list[dict[str, Any]]:
    """Coleta o histórico das últimas 20 execuções de pipelines registradas na plataforma.

    Returns:
        list[dict[str, Any]]: Lista de documentos normalizados de execuções de pipeline.
    """
    engine = get_engine()
    documentos = []
    with engine.connect() as conn:
        resultado = conn.execute(
            text("""
                SELECT source, status, rows_processed, finished_at
                FROM ingestion_batch
                ORDER BY finished_at DESC
                LIMIT 20
            """)
        ).fetchall()
        for linha in resultado:
            conteudo = (
                f"Fonte: {linha[0]}\n"
                f"Status: {linha[1]}\n"
                f"Linhas processadas: {linha[2]}\n"
                f"Finalizado em: {linha[3]}"
            )
            documentos.append(
                criar_documento(
                    titulo=f"Execução de pipeline: {linha[0]}",
                    conteudo=conteudo,
                    fonte="pipeline_run",
                    metadados={"source": linha[0]},
                )
            )
    return documentos


def coletar_documentos_rag(diretorio_saida: Path) -> dict[str, Any]:
    """Orquestra a coleta completa de todas as fontes de contexto para o RAG.

    Args:
        diretorio_saida: Pasta onde os documentos JSON normalizados serão salvos.

    Returns:
        dict[str, Any]: Dicionário contendo o total de documentos coletados e salvos.
    """
    logger.info("Iniciando coleta de documentos RAG")

    # Localiza a raiz do repositório a partir da posição deste arquivo (src/cinelake/rag/collector.py)
    raiz = Path(__file__).resolve().parents[3]

    documentos = []
    documentos += coletar_adrs(raiz / "docs")
    documentos += coletar_runbooks(raiz / "docs")
    documentos += coletar_modelos_dbt(raiz / "dbt_project")
    documentos += coletar_contratos(raiz / "src/cinelake/data_quality/data_contracts")
    documentos += coletar_schema_tabelas()
    documentos += coletar_ultimas_execucoes()

    # Salva todos os documentos em arquivos JSON individuais no diretório de saída
    salvar_documentos(documentos, diretorio_saida)

    logger.info("Coleta concluída. Total de documentos: %d", len(documentos))
    return {"total_documentos": len(documentos)}

