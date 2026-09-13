"""Avaliação do agente RAG + MCP."""

# Importa o módulo json da biblioteca padrão para manipulação e persistência de arquivos JSON
import json

# Importa o módulo nativo de logging para emissão de mensagens informativas e erros
import logging

# Importa o módulo nativo time para medição de latência e tempo de resposta das chamadas
import time

# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos de arquivos
from pathlib import Path

# Importa Any e cast do módulo typing para tipagem estática rigorosa exigida pelo mypy
from typing import Any, cast

# Importa o cliente HTTP httpx para disparar requisições para a API do assistente RAG
import httpx

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Função auxiliar que lê e carrega a lista de perguntas de teste do dataset JSON
def _carregar_dataset(caminho: Path) -> list[dict[str, Any]]:
    # Abre o arquivo do dataset com codificação UTF-8
    with caminho.open("r", encoding="utf-8") as f:
        # Carrega o JSON e retorna a lista associada à chave 'perguntas'
        dados: dict[str, Any] = json.load(f)
        return cast(list[dict[str, Any]], dados["perguntas"])


# Função auxiliar que dispara uma requisição POST para a rota /ask da API RAG
def _chamar_api(pergunta: str, top_k: int = 5) -> dict[str, Any]:
    """Chama o endpoint /ask e retorna a resposta."""
    # Define a URL de destino da API RAG local
    url = "http://127.0.0.1:8001/ask"
    # Monta o corpo JSON da requisição com a pergunta e o parâmetro top_k
    payload = {"texto": pergunta, "top_k": top_k}
    # Cria o contexto do cliente httpx com timeout seguro de 60 segundos
    with httpx.Client(timeout=60) as client:
        # Envia a requisição HTTP POST para o endpoint
        resposta = client.post(url, json=payload)
        # Dispara exceção caso a resposta retorne código de erro HTTP (ex: 4xx ou 5xx)
        resposta.raise_for_status()
        # Retorna o corpo da resposta convertido em dicionário
        return cast(dict[str, Any], resposta.json())


# Função principal que executa a avaliação completa do agente RAG + MCP
def avaliar_agente(dataset_path: Path, top_k: int = 5) -> dict[str, Any]:
    """Executa a avaliação do agente."""
    # Registra no log o início da avaliação do agente
    logger.info("Iniciando avaliação do agente")
    # Carrega a lista de perguntas do arquivo de dataset informado
    perguntas = _carregar_dataset(dataset_path)

    # Contabiliza o número total de perguntas a serem avaliadas
    total = len(perguntas)
    # Inicializa o contador de acertos na seleção da ferramenta MCP
    acertos_ferramenta = 0
    # Inicializa o contador de acertos na recuperação dos documentos esperados
    acertos_documento = 0
    # Lista para armazenar as pontuações de recall de documentos de cada pergunta
    recalls = []
    # Lista para armazenar a latência em milissegundos de cada requisição
    latencias = []

    # Lista para acumular o detalhamento minucioso do resultado de cada pergunta
    detalhes = []

    # Itera sobre cada pergunta do dataset de avaliação
    for p in perguntas:
        # Marca o timestamp de início da requisição para cálculo de latência
        inicio = time.time()
        # Bloco protegido para capturar falhas de comunicação com o endpoint
        try:
            # Executa a chamada à API do assistente enviando a pergunta
            resposta = _chamar_api(p["texto"], top_k=top_k)
        # Trata exceções em caso de falha de conexão ou erro no servidor
        except Exception as exc:
            # Registra no log o erro ocorrido para a pergunta avaliada
            logger.error("Erro ao chamar /ask para %s: %s", p["id"], exc)
            # Adiciona o registro de erro na lista de detalhes
            detalhes.append({"pergunta_id": p["id"], "erro": str(exc)})
            # Passa para a próxima pergunta da lista
            continue
        # Calcula a latência da requisição convertendo o tempo para milissegundos
        latencia = (time.time() - inicio) * 1000
        # Adiciona o tempo medido à lista de latências
        latencias.append(latencia)

        # Extrai o dicionário de contexto retornado pela resposta da API
        contexto = resposta.get("contexto", {})
        # Extrai o nome da ferramenta MCP acionada pelo agente
        ferramenta = contexto.get("ferramenta_utilizada")
        # Extrai a lista de títulos dos documentos recuperados na busca vetorial
        docs = [d.get("titulo") for d in contexto.get("documentos_recuperados", [])]

        # Compara se a ferramenta utilizada pelo agente é igual à esperada
        ferramenta_ok = ferramenta == p["ferramenta_esperada"]
        # Incrementa o contador de acertos de ferramenta caso positivo
        if ferramenta_ok:
            acertos_ferramenta += 1

        # Obtém o conjunto de documentos esperados definidos no dataset de teste
        docs_esperados = set(p.get("documentos_esperados", []))
        # Verifica se havia documentos esperados para esta pergunta
        if docs_esperados:
            # Converte os documentos retornados em conjunto (set)
            recuperados = set(docs)
            # Calcula a quantidade de documentos em comum (interseção)
            hits = len(docs_esperados & recuperados)
            # Se encontrou ao menos um documento esperado, contabiliza como hit
            if hits > 0:
                acertos_documento += 1
            # Calcula o recall da pergunta e adiciona na lista
            recalls.append(hits / len(docs_esperados))

        # Adiciona o relatório detalhado da pergunta avaliada
        detalhes.append(
            {
                "pergunta_id": p["id"],
                "ferramenta_esperada": p["ferramenta_esperada"],
                "ferramenta_obtida": ferramenta,
                "ferramenta_ok": ferramenta_ok,
                "documentos_esperados": list(docs_esperados),
                "documentos_recuperados": docs,
                "latencia_ms": round(latencia, 2),
            }
        )

    # Consolida as métricas finais agregadas do agente
    resumo = {
        "total_perguntas": total,
        "tool_selection_accuracy": acertos_ferramenta / total if total else 0.0,
        "document_hit_rate": acertos_documento / total if total else 0.0,
        "document_recall_medio": sum(recalls) / len(recalls) if recalls else 0.0,
        "latencia_media_ms": sum(latencias) / len(latencias) if latencias else 0.0,
    }

    # Salvar resultados
    # Define o caminho do arquivo onde o relatório consolidado será persistido
    saida = Path("docs/agent_evaluation/resultados.json")
    # Garante a criação do diretório docs/agent_evaluation caso não exista
    saida.parent.mkdir(parents=True, exist_ok=True)
    # Abre o arquivo em modo de escrita com codificação UTF-8
    with saida.open("w", encoding="utf-8") as f:
        # Escreve o JSON estruturado contendo resumo e detalhes
        json.dump({"resumo": resumo, "detalhes": detalhes}, f, ensure_ascii=False, indent=2)

    # Registrar no MLflow
    # Bloco protegido para registrar as métricas apuradas no servidor MLflow
    try:
        # Importação da função de rastreamento de métricas no MLflow
        from cinelake.mlops.tracking import log_parametros_e_metricas

        # Registra os parâmetros e as métricas no experimento 'agent_evaluation'
        log_parametros_e_metricas(
            experimento_nome="agent_evaluation",
            parametros={"top_k": top_k, "total_perguntas": total},
            metricas=resumo,
        )
    # Trata exceções caso o MLflow não esteja respondendo
    except Exception as exc:
        # Registra aviso no log informando que o envio ao MLflow falhou
        logger.warning("Falha ao registrar no MLflow: %s", exc)

    # Registra no log a finalização da avaliação e as métricas calculadas
    logger.info("Avaliação do agente concluída: %s", resumo)
    # Retorna o dicionário de resumo das métricas
    return resumo
