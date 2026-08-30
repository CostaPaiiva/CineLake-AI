# Módulo de API FastAPI que integra busca vetorial (RAG) e chamadas de ferramentas (MCP).
"""API FastAPI que combina RAG e MCP para responder perguntas."""

# Importa o módulo nativo de logging para emissão de mensagens de diagnóstico e erro.
import logging

# Importa o tipo Any da biblioteca typing para tipagem genérica.
from typing import Any

# Importa a classe principal FastAPI e a exceção HTTPException para tratamento de erros HTTP.
from fastapi import FastAPI, HTTPException

# Importa BaseModel do Pydantic para validação e definição dos esquemas das requisições.
from pydantic import BaseModel

# Importa a função de invocação de ferramentas MCP do cliente MCP local.
from cinelake.rag.mcp_client import invocar_ferramenta_mcp

# Importa a função de busca por similaridade vetorial do módulo retriever.
from cinelake.rag.retriever import buscar_documentos_similares

# Define a instância do logger associada a este módulo.
logger = logging.getLogger(__name__)

# Inicializa a aplicação FastAPI configurando o título e a versão da API.
app = FastAPI(title="CineLake AI - RAG + MCP API", version="0.1.0")


# Define a estrutura de dados de entrada da requisição usando Pydantic.
class Pergunta(BaseModel):  # type: ignore[misc]
    # Docstring da classe Pergunta detalhando sua finalidade.
    """Modelo de entrada para a API."""

    # Campo obrigatório contendo o texto da pergunta do usuário.
    texto: str
    # Campo opcional para definir o limite de documentos parecidos (padrão é 5).
    top_k: int = 5
    # Campo opcional para lista de ferramentas adicionais solicitadas pelo cliente (padrão lista vazia).
    incluir_ferramentas: list[str] = []


# Define a função utilitária interna para detectar qual ferramenta MCP deve ser chamada com base na pergunta.
def _detectar_ferramenta(pergunta: str) -> str | None:
    # Docstring explicativa informando o mapeamento de perguntas para ferramentas MCP.
    """
    Mapeia a pergunta para uma ferramenta MCP apropriada.

    Retorna o nome da ferramenta ou None se nenhuma se aplicar.
    """
    # Converte o texto da pergunta para letras minúsculas a fim de facilitar a busca de palavras-chave.
    p = pergunta.lower()
    # Verifica se alguma palavra relativa à saúde da plataforma está presente na pergunta.
    if any(palavra in p for palavra in ["saúde", "status", "health", "plataforma"]):
        # Retorna o nome da ferramenta que busca a saúde da plataforma.
        return "get_platform_health"
    # Verifica se alguma palavra relativa ao status de pipelines está presente na pergunta.
    elif any(palavra in p for palavra in ["pipeline", "falhou", "execução"]):
        # Retorna o nome da ferramenta que verifica o status do pipeline.
        return "get_pipeline_status"
    # Verifica se alguma palavra relativa ao atraso ou atualização de dados está presente.
    elif any(palavra in p for palavra in ["freshness", "atrasado", "atrasada"]):
        # Retorna o nome da ferramenta que avalia a atualização (freshness) dos dados.
        return "get_data_freshness"
    # Verifica se alguma palavra relativa a falhas de qualidade dos dados está presente.
    elif any(palavra in p for palavra in ["qualidade", "falhas"]):
        # Retorna o nome da ferramenta que consulta falhas na qualidade dos dados.
        return "get_data_quality_failures"
    # Verifica se alguma palavra relativa ao esquema ou tabelas do banco está presente.
    elif any(palavra in p for palavra in ["schema", "tabela"]):
        # Retorna o nome da ferramenta que obtém o esquema da tabela.
        return "get_table_schema"
    # Retorna None caso nenhuma palavra-chave corresponda às ferramentas conhecidas.
    return None


# Define a rota POST '/ask' da API FastAPI para responder perguntas combinando RAG e MCP.
@app.post("/ask", summary="Pergunta à plataforma combinando RAG e MCP")
def ask(pergunta: Pergunta) -> dict[str, Any]:
    # Docstring detalhando o fluxo do endpoint /ask.
    """Recebe pergunta, recupera documentos e invoca ferramentas MCP."""
    # Bloco try para capturar eventuais exceções ocorridas durante o processamento.
    try:
        # Comentário indicando a primeira etapa do fluxo.
        # 1. Recupera documentos relevantes via RAG
        # Realiza a busca vetorial por documentos similares à pergunta do usuário.
        documentos = buscar_documentos_similares(pergunta.texto, top_k=pergunta.top_k)
        # Formata os documentos recuperados criando uma lista de resumos truncados.
        contexto_docs = [
            # Cria um dicionário para cada documento com título, fonte, score de similaridade e trecho inicial.
            {
                # Atribui o título do documento.
                "titulo": doc["titulo"],
                # Atribui a fonte de origem do documento.
                "fonte": doc["fonte"],
                # Atribui o nível de similaridade encontrado.
                "similaridade": doc["similaridade"],
                # Limita o trecho do conteúdo aos primeiros 500 caracteres. # limitar tamanho
                "trecho": doc["conteudo"][:500],
            }
            # Itera sobre cada documento da lista retornada pelo retriever.
            for doc in documentos
        ]

        # Comentário indicando a segunda etapa do fluxo.
        # 2. Detecta ferramenta a ser chamada
        # Tenta detectar automaticamente uma ferramenta MCP adequada para a pergunta.
        ferramenta = _detectar_ferramenta(pergunta.texto)
        # Inicializa a variável do resultado da ferramenta como None.
        resultado_ferramenta = None
        # Verifica se alguma ferramenta foi identificada para execução.
        if ferramenta:
            # Invoca a ferramenta MCP identificada e obtém o resultado.
            resultado_ferramenta = invocar_ferramenta_mcp(ferramenta)

        # Comentário indicando a terceira etapa do fluxo.
        # 3. Monta contexto combinado
        # Monta o objeto de contexto unificado reunindo a pergunta, documentos e resultado da ferramenta.
        contexto = {
            # Armazena a pergunta original do usuário.
            "pergunta": pergunta.texto,
            # Armazena a lista de documentos recuperados via RAG.
            "documentos_recuperados": contexto_docs,
            # Armazena o nome da ferramenta MCP utilizada (ou None).
            "ferramenta_utilizada": ferramenta,
            # Armazena a resposta retornada pela ferramenta MCP (ou None).
            "resultado_ferramenta": resultado_ferramenta,
        }

        # Retorna a resposta HTTP contendo o status ok, o contexto consolidado e uma mensagem explicativa.
        return {
            # Status de sucesso do processamento.
            "status": "ok",
            # Objeto de contexto montado para a próxima fase.
            "contexto": contexto,
            # Mensagem indicando que o contexto está pronto para consumo por modelos LLM.
            "mensagem": "Contexto pronto para geração por LLM (não implementado nesta fase).",
        }

    # Captura qualquer erro/exceção genérica durante a execução da rota.
    except Exception as exc:
        # Grava o log detalhado de exceção contendo a pilha de erros (traceback).
        logger.exception("Erro ao processar pergunta")
        # Lança a exceção do FastAPI retornando código HTTP 500 com a mensagem de erro.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
