# Módulo responsável por funções de recuperação de documentos usando a extensão pgvector.
"""Funções de recuperação de documentos usando pgvector."""

# Importa o módulo nativo de logging para registro de mensagens de log.
import logging
# Importa o tipo Any do módulo typing para anotações de tipos genéricos.
from typing import Any

# Importa a classe SentenceTransformer da biblioteca sentence_transformers para geração de vetores de embeddings.
from sentence_transformers import SentenceTransformer
# Importa a função text do SQLAlchemy para construir consultas SQL em texto bruto.
from sqlalchemy import text

# Importa a função get_engine do módulo de banco de dados do CineLake para obter a conexão/engine da base de dados.
from cinelake.db import get_engine

# Define o logger para este arquivo utilizando o nome do módulo atual.
logger = logging.getLogger(__name__)

# Comentário explicativo sobre o modelo de embeddings utilizado.
# Modelo de embeddings (mesmo usado na indexação)
# Carrega e inicializa o modelo pré-treinado "all-MiniLM-L6-v2" para vetorização de textos.
MODELO = SentenceTransformer("all-MiniLM-L6-v2")


# Define a função para gerar o embedding numérico a partir de uma pergunta em texto.
def gerar_embedding(pergunta: str) -> list[float]:
    # Docstring da função explicitando que gera um embedding normalizado para a pergunta.
    """Gera embedding normalizado para a pergunta."""
    # Gera os vetores numéricos (embeddings) normalizados a partir do texto da pergunta.
    embedding = MODELO.encode(pergunta, normalize_embeddings=True)
    # Converte o array NumPy retornado pelo modelo para uma lista padrão de números flutuantes e a retorna.
    return embedding.tolist()


# Define a função para realizar a busca por documentos mais similares no pgvector.
def buscar_documentos_similares(pergunta: str, top_k: int = 5) -> list[dict[str, Any]]:
    # Docstring da função explicitando que busca os top_k documentos mais parecidos no pgvector.
    """Busca os top_k documentos mais similares no pgvector."""
    # Gera o embedding numérico correspondente à pergunta informada pelo usuário.
    embedding = gerar_embedding(pergunta)
    # Obtém a instância da engine de conexão do banco de dados PostgreSQL/pgvector.
    engine = get_engine()

    # Comentário explicativo sobre o cálculo de similaridade de cosseno com o operador do pgvector.
    # Consulta por similaridade de cosseno (1 - <=>)
    # Define a query SQL para selecionar dados da tabela rag_documents e calcular a similaridade de cosseno.
    query = text("""
        SELECT titulo, conteudo, fonte, metadados,
               1 - (embedding <=> :embedding) AS similaridade
        FROM rag_documents
        ORDER BY similaridade DESC
        LIMIT :top_k
    """)

    # Abre um bloco de conexão com o banco de dados usando gerenciador de contexto (with).
    with engine.connect() as conn:
        # Executa a instrução SQL passando os parâmetros do embedding e limite (top_k), trazendo todos os resultados.
        resultado = conn.execute(
            query,
            {"embedding": embedding, "top_k": top_k},
        ).fetchall()

    # Inicializa a lista vazia para armazenar os documentos formatados como dicionários.
    documentos = []
    # Itera sobre cada linha retornada pela consulta no banco de dados.
    for linha in resultado:
        # Adiciona um dicionário formatado à lista de documentos com as informações recuperadas da linha.
        documentos.append(
            {
                # Atribui o título do documento (coluna 0 do resultado).
                "titulo": linha[0],
                # Atribui o conteúdo textual do documento (coluna 1 do resultado).
                "conteudo": linha[1],
                # Atribui a fonte de origem do documento (coluna 2 do resultado).
                "fonte": linha[2],
                # Atribui os metadados associados ao documento (coluna 3 do resultado).
                "metadados": linha[3],
                # Atribui a pontuação de similaridade convertida para float (coluna 4 do resultado).
                "similaridade": float(linha[4]),
            }
        )

    # Retorna a lista final contendo os documentos mais similares encontrados.
    return documentos
