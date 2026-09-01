"""Pipeline de indexação e geração de embeddings de documentos para o pgvector RAG."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import Connection, text

from cinelake.db import get_engine

logger = logging.getLogger(__name__)

# Carrega o modelo de embeddings pré-treinado all-MiniLM-L6-v2
MODELO = SentenceTransformer("all-MiniLM-L6-v2")
DIMENSAO_EMBEDDING = 384  # Tamanho do vetor resultante gerado pelo modelo


def _calcular_source_id(titulo: str, fonte: str) -> str:
    """Gera um identificador único determinístico (hash SHA-256) para o documento.

    Args:
        titulo: Título do documento.
        fonte: Origem da informação.

    Returns:
        str: Hexdigest SHA-256 do par título + fonte.
    """
    hash_obj = hashlib.sha256(f"{titulo}|{fonte}".encode())
    return hash_obj.hexdigest()


def _gerar_embedding(conteudo: str) -> list[float]:
    """Gera o vetor de embeddings normalizado para o conteúdo textual fornecido.

    Args:
        conteudo: Texto legível do documento.

    Returns:
        list[float]: Vetor de 384 números de ponto flutuante.
    """
    embedding = MODELO.encode(conteudo, normalize_embeddings=True)
    return [float(x) for x in embedding.tolist()]


def _registrar_batch(
    conn: Connection, status: str, total_processado: int, erro: str | None = None
) -> int:
    """Registra a execução do lote de indexação RAG na tabela de auditoria `ingestion_batch`.

    Args:
        conn: Conexão ativa com o banco PostgreSQL.
        status: Status da execução ('running', 'success', 'failed').
        total_processado: Quantidade de documentos processados.
        erro: Mensagem de erro caso haja falha.

    Returns:
        int: O identificador único batch_id gerado.
    """
    agora = datetime.now(timezone.utc)
    resultado = conn.execute(
        text("""
            INSERT INTO ingestion_batch
            (source, status, started_at, rows_processed, rows_inserted, error_message)
            VALUES ('rag_indexing', :status, :started_at, :rows_processed, :rows_inserted, :error_message)
            RETURNING batch_id
        """),
        {
            "status": status,
            "started_at": agora,
            "rows_processed": total_processado,
            "rows_inserted": total_processado,  # Simplificação (considera inserções)
            "error_message": erro,
        },
    )
    val = resultado.scalar()
    return int(val) if val is not None else -1


def indexar_documentos(diretorio_documentos: Path) -> dict[str, Any]:
    """Lê documentos JSON normalizados e realiza o upsert no PostgreSQL (pgvector).

    Args:
        diretorio_documentos: Diretório contendo os arquivos JSON criados no processo de coleta.

    Returns:
        dict[str, Any]: Resumo contendo total de documentos processados e inseridos/atualizados.
    """
    logger.info("Iniciando indexação de documentos RAG")

    engine = get_engine()
    total_processado = 0
    total_inserido = 0

    with engine.begin() as conn:
        _registrar_batch(conn, "running", total_processado)

        try:
            for arquivo in sorted(diretorio_documentos.glob("doc_*.json")):
                with arquivo.open("r", encoding="utf-8") as f:
                    doc = json.load(f)

                titulo = doc["titulo"]
                conteudo = doc["conteudo"]
                fonte = doc["fonte"]
                metadados = doc.get("metadados", {})
                source_id = _calcular_source_id(titulo, fonte)

                # Gera embedding usando o modelo SentenceTransformer
                embedding = _gerar_embedding(conteudo)
                total_processado += 1

                # Realiza o Upsert (INSERT ON CONFLICT UPDATE) na tabela rag_documents
                conn.execute(
                    text("""
                        INSERT INTO rag_documents
                        (titulo, conteudo, fonte, metadados, embedding, source_id)
                        VALUES (:titulo, :conteudo, :fonte, :metadados, :embedding, :source_id)
                        ON CONFLICT (source_id)
                        DO UPDATE SET
                            titulo = EXCLUDED.titulo,
                            conteudo = EXCLUDED.conteudo,
                            fonte = EXCLUDED.fonte,
                            metadados = EXCLUDED.metadados,
                            embedding = EXCLUDED.embedding
                    """),
                    # Passa os parâmetros da instrução SQL convertendo o embedding para string do tipo vetor
                    {
                        # Atribui o título do documento
                        "titulo": titulo,
                        # Atribui o conteúdo textual do documento
                        "conteudo": conteudo,
                        # Atribui a fonte de origem do documento
                        "fonte": fonte,
                        # Serializa os metadados do documento em formato JSON string
                        "metadados": json.dumps(metadados, ensure_ascii=False),
                        # Converte a lista de números do embedding para string no formato de vetor reconhecido pelo pgvector
                        "embedding": str(embedding),
                        # Atribui o identificador único do lote do documento
                        "source_id": source_id,
                    },
                )
                total_inserido += 1

            _registrar_batch(conn, "success", total_processado)

        except Exception as exc:
            logger.exception("Erro durante indexação RAG")
            _registrar_batch(conn, "failed", total_processado, str(exc))
            raise

    logger.info("Indexação concluída. Documentos processados: %d", total_processado)
    return {"total_processado": total_processado, "total_inserido": total_inserido}
