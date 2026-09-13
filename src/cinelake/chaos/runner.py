"""Runner do Chaos Lab."""

# Importa o módulo json da biblioteca padrão para gravação de relatórios em disco
import json

# Importa o módulo nativo de logging para emissão de logs e diagnósticos
import logging
from collections.abc import Callable

# Importa datetime e timezone para registro preciso de timestamps UTC de início e término dos testes
from datetime import datetime, timezone

# Importa Path da biblioteca pathlib para manipulação orientada a objetos de caminhos e diretórios
from pathlib import Path

# Importa Any e Callable do módulo typing para tipagem estática rigorosa exigida pelo mypy
from typing import Any

# Importa todos os cenários de injeção de falhas controladas
from cinelake.chaos.scenarios import (
    cenario_dlq_event,
    cenario_high_latency,
    cenario_kafka_down,
    cenario_mcp_down,
    cenario_minio_down,
    cenario_pipeline_falha,
    cenario_postgres_down,
)

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Dicionário de registro que mapeia os nomes de identificação aos métodos de execução de cada cenário
CENARIOS: dict[str, Callable[..., dict[str, Any]]] = {
    # Mapeia o teste de queda do PostgreSQL
    "postgres_down": cenario_postgres_down,
    # Mapeia o teste de queda do MinIO S3
    "minio_down": cenario_minio_down,
    # Mapeia o teste de queda do broker Kafka
    "kafka_down": cenario_kafka_down,
    # Mapeia o teste de encerramento do processo MCP
    "mcp_down": cenario_mcp_down,
    # Mapeia o teste de injeção de pipeline com falha
    "pipeline_failure": cenario_pipeline_falha,
    # Mapeia o teste de envio de evento inválido para a DLQ
    "dlq_event": cenario_dlq_event,
    # Mapeia o teste de simulação de alta latência
    "high_latency": cenario_high_latency,
}


# Função responsável por disparar um cenário individual com parâmetros customizados
def executar_cenario(nome: str, **kwargs: Any) -> dict[str, Any]:
    """Executa um cenário específico."""
    # Valida se o nome do cenário informado consta no dicionário de cenários registrados
    if nome not in CENARIOS:
        # Dispara erro caso o cenário não seja reconhecido
        raise ValueError(f"Cenário desconhecido: {nome}")
    # Registra no log o início da execução do cenário
    logger.info("Executando cenário %s", nome)
    # Registra o timestamp UTC de início do teste
    inicio = datetime.now(timezone.utc)
    # Executa a função do cenário passando os argumentos correspondentes
    resultado = CENARIOS[nome](**kwargs)
    # Adiciona o timestamp ISO de início no relatório
    resultado["inicio"] = inicio.isoformat()
    # Adiciona o timestamp ISO de término no relatório
    resultado["fim"] = datetime.now(timezone.utc).isoformat()
    # Retorna o dicionário de resultados do teste
    return resultado


# Função orquestradora que executa em sequência todos os cenários de Chaos Engineering
def executar_todos_cenarios() -> list[dict[str, Any]]:
    """Executa todos os cenários e salva resultados."""
    # Lista para acumular os resultados de cada teste executado
    resultados: list[dict[str, Any]] = []
    # Itera sobre cada cenário e sua respectiva função executora
    for nome, funcao in CENARIOS.items():
        # Bloco protegido para isolar falhas individuais sem interromper a suíte completa
        try:
            # Ajusta argumentos conforme a assinatura
            # Para cenários de queda de infraestrutura, aplica duração de 20 segundos
            if nome in ("postgres_down", "minio_down", "kafka_down", "mcp_down"):
                resultado = funcao(duracao_segundos=20)
            # Para cenário de latência, injeta atraso artificial de 1000 milissegundos
            elif nome == "high_latency":
                resultado = funcao(duracao_ms=1000)
            # Para os demais cenários, executa sem parâmetros adicionais
            else:
                resultado = funcao()
            # Registra timestamp de início
            resultado["inicio"] = datetime.now(timezone.utc).isoformat()
            # Registra timestamp de encerramento
            resultado["fim"] = datetime.now(timezone.utc).isoformat()
            # Adiciona o resultado à lista
            resultados.append(resultado)
        # Captura e trata qualquer exceção lançada durante o teste
        except Exception as exc:
            # Registra no log o erro ocorrido com traceback
            logger.exception("Falha ao executar cenário %s", nome)
            # Adiciona o registro de erro na lista de resultados
            resultados.append({"cenario": nome, "erro": str(exc)})

    # Salva resultados
    # Define o caminho do arquivo JSON onde os relatórios de execução serão persistidos
    saida = Path("docs/chaos_lab/resultados.json")
    # Garante a criação do diretório docs/chaos_lab caso ainda não exista
    saida.parent.mkdir(parents=True, exist_ok=True)
    # Abre o arquivo para escrita com codificação UTF-8
    with saida.open("w", encoding="utf-8") as f:
        # Serializa os resultados em formato JSON com indentação de 2 espaços
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    # Retorna a lista completa com os relatórios gerados
    return resultados
