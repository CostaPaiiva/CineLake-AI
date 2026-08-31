"""Funções para registrar e consultar métricas de uso do RAG."""

import logging  # Importa o módulo nativo de logging para emissão de mensagens de auditoria e depuração.
from datetime import (  # Importa utilitários para obtenção de datas e horários em UTC.
    datetime,
    timezone,
)
from typing import Any  # Importa Any para anotações de tipos genéricos e flexíveis.

from sqlalchemy import (
    text,  # Importa a função text do SQLAlchemy para construção de queries SQL parametrizadas.
)

from cinelake.db import (
    get_engine,  # Importa a função que fornece o engine de conexão com o banco de dados.
)

logger = logging.getLogger(__name__)  # Instancia o logger para este módulo específico.


def registrar_consulta(  # Define a função responsável por persistir os detalhes da consulta RAG no banco de dados.
    pergunta: str,  # Texto da pergunta enviada pelo usuário.
    documentos_recuperados: list[dict[str, Any]],  # Lista de dicionários contendo os documentos recuperados no retriever.
    ferramenta_mcp: str | None,  # Nome da ferramenta MCP identificada/utilizada (ou None caso nenhuma).
    resultado_ferramenta: Any,  # Resultado retornado pela execução da ferramenta MCP (ou None).
    latencia_ms: float,  # Tempo total de execução do processamento em milissegundos.
    status_code: int = 200,  # Código de status HTTP da requisição (padrão 200).
    erro: str | None = None,  # Mensagem de erro em caso de exceção (ou None caso sucesso).
) -> None:  # Retorno void (None).
    """Registra uma consulta RAG no log."""  # Docstring descrevendo a funcionalidade da função registrar_consulta.
    engine = get_engine()  # Obtém a engine de conexão do SQLAlchemy.
    with engine.begin() as conn:  # Abre uma transação no banco com auto-commit e auto-rollback em caso de erro.
        conn.execute(  # Executa o comando de inserção de dados via query SQL pura.
            text("""
                INSERT INTO rag_query_log
                    (pergunta, documentos_recuperados, ferramenta_mcp, resultado_ferramenta, latencia_ms, status_code, erro, timestamp)
                VALUES
                    (:pergunta, :documentos, :ferramenta, :resultado, :latencia, :status, :erro, :agora)
            """),  # Query SQL utilizando binds parametrizados para evitar injeção SQL.
            {  # Dicionário mapeando os parâmetros da query para os valores recebidos na função.
                "pergunta": pergunta,  # Passa o texto da pergunta.
                "documentos": documentos_recuperados,  # Passa a lista de documentos para o campo JSONB.
                "ferramenta": ferramenta_mcp,  # Passa o identificador da ferramenta MCP acionada.
                "resultado": resultado_ferramenta,  # Passa os dados do resultado da ferramenta MCP para o campo JSONB.
                "latencia": latencia_ms,  # Passa a medição da latência em ms.
                "status": status_code,  # Passa o status HTTP resultante.
                "erro": erro,  # Passa a mensagem de erro (se houver).
                "agora": datetime.now(timezone.utc),  # Passa o timestamp atual em UTC.
            },  # Fecha o dicionário de parâmetros.
        )  # Fecha a execução da query conn.execute.
    logger.debug("Consulta RAG registrada: %s", pergunta[:50])  # Registra em nível DEBUG no log que a consulta foi salva.


def obter_metricas_rag() -> dict[str, Any]:  # Define a função que extrai agregações e métricas de desempenho do RAG.
    """Agrega métricas básicas do uso do RAG."""  # Docstring da função obter_metricas_rag.
    engine = get_engine()  # Obtém a engine de conexão do banco de dados.
    with engine.connect() as conn:  # Abre uma conexão de leitura com o banco de dados.
        total = conn.execute(text("SELECT COUNT(*) FROM rag_query_log")).scalar()  # Conta o número total de consultas registradas na tabela.
        latencia_media = conn.execute(  # Executa query para calcular a latência média das requisições registradas.
            text("SELECT AVG(latencia_ms) FROM rag_query_log WHERE latencia_ms IS NOT NULL")  # Query SQL calculando a média descartando nulos.
        ).scalar()  # Extrai o valor escalar retornado pela query.
        erros = conn.execute(  # Executa query para contar quantas consultas resultaram em erro ou status >= 400.
            text("SELECT COUNT(*) FROM rag_query_log WHERE status_code >= 400 OR erro IS NOT NULL")  # Query SQL para contagem de falhas.
        ).scalar()  # Extrai a quantidade total de erros.
        rows_ferramenta = conn.execute(
            text("""
                SELECT ferramenta_mcp, COUNT(*)
                FROM rag_query_log
                WHERE ferramenta_mcp IS NOT NULL
                GROUP BY ferramenta_mcp
            """)
        ).fetchall()
        consultas_por_ferramenta: dict[str, int] = {
            str(row[0]): int(row[1]) for row in rows_ferramenta
        }
        ultimas_consultas = [  # Constrói uma lista contendo as 10 consultas mais recentes para auditoria rápida.
            dict(row)  # Converte cada linha retornada em um dicionário chave-valor.
            for row in conn.execute(  # Executa a query de busca ordenada por tempo.
                text("""
                    SELECT pergunta, ferramenta_mcp, latencia_ms, status_code, timestamp
                    FROM rag_query_log
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)  # Retorna as últimas 10 consultas registradas no sistema.
            ).mappings()  # Utiliza mappings() para permitir o acesso direto às colunas como dicionário.
        ]  # Fecha a list comprehension.

    return {  # Retorna o dicionário consolidado com todos os indicadores de observabilidade do RAG.
        "total_consultas": total,  # Total absoluto de perguntas processadas.
        "latencia_media_ms": float(latencia_media) if latencia_media else None,  # Média de latência convertida em float ou None se vazio.
        "total_erros": erros,  # Quantidade de falhas registradas.
        "consultas_por_ferramenta": consultas_por_ferramenta,  # Dicionário com a distribuição de uso das ferramentas MCP.
        "ultimas_consultas": ultimas_consultas,  # Histórico das últimas 10 consultas processadas.
    }  # Fecha o retorno do dicionário.
