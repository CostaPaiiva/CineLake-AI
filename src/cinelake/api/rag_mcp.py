"""API FastAPI que combina RAG e MCP para responder perguntas."""

import logging  # Importa o módulo nativo para geração de logs de execução e erros.
import time  # Importa o módulo de manipulação de tempo para cálculo de latência.
from typing import Any  # Importa o tipo genérico Any para anotações de tipagem.

from fastapi import FastAPI, HTTPException  # Importa a classe FastAPI para criação da API REST e HTTPException para tratamento de erros.
from pydantic import BaseModel  # Importa BaseModel do Pydantic para validação e serialização dos dados de entrada.

from cinelake.rag.mcp_client import invocar_ferramenta_mcp  # Importa a função que despacha chamadas para o servidor MCP local.
from cinelake.rag.observability import obter_metricas_rag, registrar_consulta  # Importa funções de observabilidade e métricas do RAG.
from cinelake.rag.retriever import buscar_documentos_similares  # Importa a função que realiza a busca semântica por similaridade de embeddings.

logger = logging.getLogger(__name__)  # Instancia o logger específico deste módulo.

app = FastAPI(title="CineLake AI - RAG + MCP API", version="0.2.0")  # Inicializa o aplicativo FastAPI definindo o título e versão 0.2.0.


class Pergunta(BaseModel):  # Define o schema Pydantic para o payload JSON recebido nas requisições da rota /ask.
    """Modelo de entrada para a API."""  # Docstring descrevendo o modelo de dados de entrada da pergunta.

    texto: str  # Campo obrigatório contendo o texto da pergunta submetida pelo usuário.
    top_k: int = 5  # Quantidade máxima de documentos similares a recuperar no RAG (padrão 5).
    incluir_ferramentas: list[str] = []  # Lista opcional de nomes de ferramentas MCP a serem consideradas.


def _detectar_ferramenta(pergunta: str) -> str | None:  # Define a função auxiliar para mapeamento baseado em palavras-chave da pergunta.
    """Mapeia a pergunta para uma ferramenta MCP apropriada."""  # Docstring descrevendo a detecção de intenção para ferramentas MCP.
    p = pergunta.lower()  # Converte a pergunta inteira para minúsculas para busca insensível a maiúsculas/minúsculas.
    if any(palavra in p for palavra in ["saúde", "status", "health", "plataforma"]):  # Verifica se trata de saúde global da plataforma.
        return "get_platform_health"  # Retorna o identificador da ferramenta MCP de saúde da plataforma.
    elif any(palavra in p for palavra in ["pipeline", "falhou", "execução"]):  # Verifica se trata de status de execução de pipelines.
        return "get_pipeline_status"  # Retorna o identificador da ferramenta MCP de status de pipelines.
    elif any(palavra in p for palavra in ["freshness", "atrasado", "atrasada"]):  # Verifica se trata de atraso ou defasagem de dados.
        return "get_data_freshness"  # Retorna o identificador da ferramenta MCP de freshness de tabelas.
    elif any(palavra in p for palavra in ["qualidade", "falhas"]):  # Verifica se trata de falhas e checagens de qualidade de dados.
        return "get_data_quality_failures"  # Retorna o identificador da ferramenta MCP de qualidade de dados.
    elif any(palavra in p for palavra in ["schema", "tabela"]):  # Verifica se trata de estrutura ou esquema de tabelas do banco.
        return "get_table_schema"  # Retorna o identificador da ferramenta MCP de schemas de tabelas.
    return None  # Retorna None caso nenhuma correspondência com ferramentas seja encontrada.


@app.post("/ask", summary="Pergunta à plataforma combinando RAG e MCP")  # Declara o endpoint POST na rota /ask da aplicação FastAPI.
def ask(pergunta: Pergunta) -> dict[str, Any]:  # Define a função controladora da rota /ask que recebe o objeto Pergunta.
    """Recebe pergunta, recupera documentos e invoca ferramentas MCP."""  # Docstring da rota /ask.
    inicio = time.time()  # Registra o timestamp inicial para medição de latência da resposta.
    status_code = 200  # Define o código de status HTTP padrão da operação como 200 (OK).
    erro = None  # Inicializa a variável de registro de erros como None.
    documentos = []  # Inicializa a lista de documentos recuperados vazia.
    ferramenta = None  # Inicializa o nome da ferramenta como None.
    resultado_ferramenta = None  # Inicializa o resultado retornado pela ferramenta como None.

    try:  # Inicia o bloco protegido de execução do fluxo de RAG e MCP.
        # 1. Recupera documentos relevantes via RAG
        documentos = buscar_documentos_similares(pergunta.texto, top_k=pergunta.top_k)  # Executa a busca vetorial no pgvector.
        contexto_docs = [  # Monta a lista formatada de trechos e metadados dos documentos recuperados.
            {  # Abre dicionário para cada documento individual recuperado.
                "titulo": doc["titulo"],  # Título do documento recuperado.
                "fonte": doc["fonte"],  # Fonte de origem do documento (ADR, Runbook, Schema, etc.).
                "similaridade": doc["similaridade"],  # Score de similaridade de cosseno retornado pelo embedding.
                "trecho": doc["conteudo"][:500],  # Recorta os primeiros 500 caracteres do conteúdo textual do documento.
            }  # Fecha o dicionário do documento.
            for doc in documentos  # Itera sobre a lista de documentos retornada pela busca vetorial.
        ]  # Fecha a compreensão de lista.

        # 2. Detecta ferramenta a ser chamada
        ferramenta = _detectar_ferramenta(pergunta.texto)  # Detecta se alguma ferramenta MCP deve ser chamada para a pergunta.
        if ferramenta:  # Se uma ferramenta válida foi identificada para a pergunta.
            resultado_ferramenta = invocar_ferramenta_mcp(ferramenta)  # Executa a chamada à ferramenta via cliente MCP.

        # 3. Monta contexto combinado
        contexto = {  # Monta o dicionário com o contexto completo pronto para o LLM.
            "pergunta": pergunta.texto,  # Pergunta original submetida pelo usuário.
            "documentos_recuperados": contexto_docs,  # Lista com os documentos de contexto relevantes encontrados.
            "ferramenta_utilizada": ferramenta,  # Nome da ferramenta MCP invocada.
            "resultado_ferramenta": resultado_ferramenta,  # Dados retornados pela ferramenta MCP em tempo real.
        }  # Fecha o dicionário de contexto consolidado.

        return {  # Retorna a resposta da requisição com status de sucesso.
            "status": "ok",  # Status da resposta.
            "contexto": contexto,  # Payload consolidado do contexto recuperado.
            "mensagem": "Contexto pronto para geração por LLM (não implementado nesta fase).",  # Mensagem explicativa.
        }  # Fecha a estrutura do retorno.

    except Exception as exc:  # Captura qualquer exceção durante a execução do pipeline.
        logger.exception("Erro ao processar pergunta")  # Registra no log de aplicação a exceção completa com traceback.
        status_code = 500  # Atualiza o status HTTP para 500 (Internal Server Error).
        erro = str(exc)  # Converte a exceção para texto para registro no log de observabilidade.
        raise HTTPException(status_code=500, detail=str(exc))  # Relança como erro HTTP para resposta ao cliente da API.

    finally:  # Bloco executado obrigatoriamente tanto em caso de sucesso quanto de falha.
        latencia_ms = (time.time() - inicio) * 1000  # Calcula o tempo total decorrido em milissegundos.
        try:  # Bloco protegido para gravação do log de auditoria no banco de dados.
            registrar_consulta(  # Invoca a função que grava a consulta na tabela rag_query_log.
                pergunta=pergunta.texto,  # Texto da pergunta recebida.
                documentos_recuperados=documentos,  # Documentos encontrados pelo retriever.
                ferramenta_mcp=ferramenta,  # Identificador da ferramenta utilizada.
                resultado_ferramenta=resultado_ferramenta,  # Resposta fornecida pela ferramenta.
                latencia_ms=latencia_ms,  # Latência total calculada em milissegundos.
                status_code=status_code,  # Código HTTP final da requisição.
                erro=erro,  # Mensagem de erro capturada ou None.
            )  # Fecha a chamada de registrar_consulta.
        except Exception as log_exc:  # Captura falha no registro de auditoria para não quebrar a requisição principal.
            logger.error("Falha ao registrar log RAG: %s", log_exc)  # Emite mensagem de erro no log.


@app.get("/rag/metrics", summary="Métricas do uso do RAG")  # Declara o endpoint GET na rota /rag/metrics para observabilidade.
def rag_metrics() -> dict[str, Any]:  # Define a função controladora que retorna estatísticas agregadas do RAG.
    """Retorna métricas agregadas do RAG."""  # Docstring da rota /rag/metrics.
    try:  # Bloco protegido para extração das métricas.
        return obter_metricas_rag()  # Executa as agregações e retorna o dicionário com métricas e histórico.
    except Exception as exc:  # Captura falhas ao consultar métricas.
        logger.exception("Erro ao obter métricas RAG")  # Registra exceção no log.
        raise HTTPException(status_code=500, detail=str(exc))  # Retorna código HTTP 500 com a mensagem do erro.
