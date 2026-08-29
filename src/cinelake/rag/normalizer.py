"""Funções para normalizar e estruturar documentos no formato padrão aceito pelo pipeline de RAG."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def criar_documento(
    titulo: str,
    conteudo: str,
    fonte: str,
    metadados: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cria e estrutura um documento normalizado com seus metadados e timestamp de coleta UTC.

    Args:
        titulo: Título ou identificador principal do documento.
        conteudo: Texto legível completo do documento.
        fonte: Origem da informação (ex: 'movielens', 'tmdb', 'dbt_docs').
        metadados: Dicionário opcional contendo atributos extras (ex: ano, gênero, id).

    Returns:
        dict[str, Any]: Estrutura serializável contendo o documento completo.
    """
    return {
        "titulo": titulo,
        "conteudo": conteudo,
        "fonte": fonte,
        "metadados": metadados or {},
        "coletado_em": datetime.now(timezone.utc).isoformat(),
    }


def salvar_documentos(documentos: list[dict[str, Any]], diretorio: Path) -> None:
    """Salva uma lista de documentos normalizados em arquivos JSON individuais no diretório especificado.

    Args:
        documentos: Lista de dicionários criados via `criar_documento`.
        diretorio: Caminho do diretório de destino onde os JSONs serão persistidos.
    """
    # Garante a criação de todas as pastas pai do diretório de destino
    diretorio.mkdir(parents=True, exist_ok=True)
    for i, doc in enumerate(documentos, start=1):
        arquivo = diretorio / f"doc_{i:04d}.json"
        with arquivo.open("w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
