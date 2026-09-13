"""Cenários de injeção de falha controlada."""

# Importa o módulo nativo de logging do Python para registro de mensagens
import logging

# Importa subprocess para executar comandos de controle de processos e containers
import subprocess

# Importa time para controle de pausas e medição de durações
import time

# Importa uuid para geração de identificadores únicos
import uuid

# Importa Any do módulo typing para garantir compatibilidade rigorosa com mypy
from typing import Any

# Importa text do SQLAlchemy para construção de instruções SQL
from sqlalchemy import text

# Importa get_engine para conexão com o PostgreSQL
from cinelake.db import get_engine

# Obtém a instância do logger correspondente ao módulo atual
logger = logging.getLogger(__name__)


# Função auxiliar para interromper a execução de um container Docker
def _docker_stop(container: str) -> None:
    """Para um container Docker."""
    # Registra no log aviso informando qual container está sendo pausado
    logger.warning("Parando container %s", container)
    # Executa o comando docker stop via subprocess sem levantar exceção
    subprocess.run(["docker", "stop", container], check=False)


# Função auxiliar para iniciar a execução de um container Docker
def _docker_start(container: str) -> None:
    """Inicia um container Docker."""
    # Registra no log informação sobre qual container está sendo iniciado
    logger.info("Iniciando container %s", container)
    # Executa o comando docker start via subprocess sem levantar exceção
    subprocess.run(["docker", "start", container], check=False)


# Cenário que simula a indisponibilidade temporária do banco de dados PostgreSQL
def cenario_postgres_down(duracao_segundos: int = 30) -> dict[str, Any]:
    """Simula queda do PostgreSQL."""
    # Registra no log o início do cenário de teste
    logger.info("Cenário: PostgreSQL down por %ds", duracao_segundos)
    # Para o container do PostgreSQL
    _docker_stop("cinelake-postgres")
    # Aguarda o tempo estipulado com o banco fora do ar
    time.sleep(duracao_segundos)
    # Inicia novamente o container do PostgreSQL
    _docker_start("cinelake-postgres")

    # Aguarda o container voltar
    # Aguarda 10 segundos adicionais para a inicialização completa do serviço PostgreSQL
    time.sleep(10)

    # Verifica recuperação
    # Variável de controle para registrar se a conexão foi restabelecida com sucesso
    recuperado = False
    # Bloco protegido para testar conexão ativa no PostgreSQL
    try:
        # Obtém a engine do banco
        engine = get_engine()
        # Abre conexão e executa uma query simples de verificação
        with engine.connect() as conn:
            # Executa SELECT 1 para testar a saúde do banco
            conn.execute(text("SELECT 1")).scalar()
        # Define recuperado como True caso a query tenha respondido
        recuperado = True
    # Trata possíveis erros caso o banco ainda não esteja aceitando conexões
    except Exception as exc:
        # Registra no log o erro ocorrido ao tentar reconectar
        logger.error("Postgres não recuperou: %s", exc)

    # Retorna o dicionário de resultados do teste
    return {
        # Identificador do cenário executado
        "cenario": "postgres_down",
        # Duração total em segundos em que o container ficou parado
        "duracao_segundos": duracao_segundos,
        # Status booleano indicando se a aplicação conseguiu se reconectar
        "recuperado": recuperado,
    }


# Cenário que simula a indisponibilidade temporária do Object Storage MinIO (S3)
def cenario_minio_down(duracao_segundos: int = 30) -> dict[str, Any]:
    """Simula queda do MinIO."""
    # Registra no log o início do cenário de indisponibilidade do MinIO
    logger.info("Cenário: MinIO down por %ds", duracao_segundos)
    # Para o container do MinIO
    _docker_stop("cinelake-minio")
    # Aguarda o tempo configurado com o MinIO desligado
    time.sleep(duracao_segundos)
    # Inicia novamente o container do MinIO
    _docker_start("cinelake-minio")
    # Aguarda 10 segundos para inicialização dos serviços internos do MinIO
    time.sleep(10)
    # Retorna o resultado do cenário executado
    return {"cenario": "minio_down", "duracao_segundos": duracao_segundos}


# Cenário que simula a indisponibilidade temporária do cluster Kafka
def cenario_kafka_down(duracao_segundos: int = 30) -> dict[str, Any]:
    """Simula queda do Kafka."""
    # Registra no log o início do teste de queda do broker Kafka
    logger.info("Cenário: Kafka down por %ds", duracao_segundos)
    # Para o container do Kafka
    _docker_stop("cinelake-kafka")
    # Aguarda o período em que o Kafka permanece fora do ar
    time.sleep(duracao_segundos)
    # Inicia novamente o container do Kafka
    _docker_start("cinelake-kafka")
    # Aguarda 15 segundos para reinicialização e reeleição do broker no cluster
    time.sleep(15)
    # Retorna o resultado consolidado do cenário
    return {"cenario": "kafka_down", "duracao_segundos": duracao_segundos}


# Cenário que simula a queda do servidor de ferramentas MCP
def cenario_mcp_down(duracao_segundos: int = 20) -> dict[str, Any]:
    """Simula queda do servidor MCP (processo local)."""
    # Registra no log a execução do cenário de queda do servidor MCP
    logger.info("Cenário: MCP down por %ds", duracao_segundos)
    # O MCP é um processo Python local; vamos matá-lo via pkill
    # Executa comando para encerrar processos que contenham 'serve-mcp'
    subprocess.run(["pkill", "-f", "serve-mcp"], check=False)
    # Aguarda o intervalo de tempo com o processo inativo
    time.sleep(duracao_segundos)
    # Emite mensagem no log instruindo o desenvolvedor a subir o MCP novamente
    logger.info("Reinicie o MCP manualmente: python -m cinelake serve-mcp")
    # Retorna o dicionário de resultado indicando necessidade de reinicialização manual
    return {
        "cenario": "mcp_down",
        "duracao_segundos": duracao_segundos,
        "reinicie_manualmente": True,
    }


# Cenário que injeta um registro de pipeline com status 'failed' na tabela de auditoria
def cenario_pipeline_falha() -> dict[str, Any]:
    """Insere um registro de falha em ingestion_batch para simular pipeline quebrado."""
    # Registra no log o início do cenário de simulação de falha de pipeline
    logger.info("Cenário: pipeline com falha")
    # Obtém a engine de conexão com o banco
    engine = get_engine()
    # Inicia bloco transacional gerenciado
    with engine.begin() as conn:
        # Executa a query de inserção de falha simulada
        conn.execute(
            text("""
                INSERT INTO ingestion_batch (source, status, started_at, finished_at, rows_processed, rows_inserted, error_message)
                VALUES ('chaos_test', 'failed', NOW(), NOW(), 0, 0, 'Falha simulada pelo Chaos Lab')
            """)
        )
    # Retorna confirmação de inserção do registro
    return {"cenario": "pipeline_failure", "inserido": True}


# Cenário que produz um evento com payload fora do schema para testar a Dead Letter Queue (DLQ)
def cenario_dlq_event() -> dict[str, Any]:
    """Envia um evento inválido ao Kafka para cair na DLQ."""
    # Registra no log o envio de mensagem com payload incorreto
    logger.info("Cenário: evento inválido → DLQ")
    # Importa módulo json para serialização
    import json

    # Importa KafkaProducer para envio da mensagem ao tópico
    from kafka import KafkaProducer

    # Importa configurações do sistema
    from cinelake.config import settings

    # Inicializa o produtor Kafka conectado aos brokers configurados
    produtor = KafkaProducer(
        # Lista de bootstrap servers do Kafka
        bootstrap_servers=settings.kafka_bootstrap_servers,
        # Função serializadora que converte dicionário Python em bytes JSON UTF-8
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    # Monta estrutura propositalmente inválida (sem event_type, user_id, movie_id, etc.)
    evento_invalido = {
        # Gera ID de evento aleatório
        "event_id": str(uuid.uuid4()),
        # faltando campos obrigatórios: event_type, user_id, movie_id, event_timestamp
        "campo_extra": "invalido",
    }
    # Envia a mensagem inválida para o tópico principal de eventos
    produtor.send("movie-events", value=evento_invalido)
    # Força a liberação dos buffers de rede do Kafka
    produtor.flush()
    # Encerra a conexão com o produtor
    produtor.close()
    # Retorna o resultado confirmando o disparo do evento inválido
    return {"cenario": "dlq_event", "enviado": True}


# Cenário que simula lentidão artificial de rede ou processamento
def cenario_high_latency(duracao_ms: int = 3000) -> dict[str, Any]:
    """Simula alta latência na API (bloqueia o processo por N ms)."""
    # Registra no log o início da injeção de atraso artificial
    logger.info("Cenário: alta latência artificial de %dms", duracao_ms)
    # Suspende a execução da thread pelo tempo correspondente em segundos
    time.sleep(duracao_ms / 1000)
    # Retorna o relatório do atraso simulado
    return {"cenario": "high_latency", "duracao_ms": duracao_ms}
