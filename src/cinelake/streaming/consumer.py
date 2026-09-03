# Módulo consumidor de streaming do Kafka com validações de dados e roteamento para Dead Letter Queue (DLQ)
"""Consumidor de eventos Kafka com validação e DLQ."""

# Importa a biblioteca json nativa para desserialização e manipulação do formato JSON
import json
# Importa a biblioteca de logging para registros de diagnostico da aplicação
import logging
# Importa datetime e timezone para formatação e manipulação de timestamps
from datetime import datetime, timezone

# Importa as classes KafkaConsumer e KafkaProducer da biblioteca oficial kafka-python
from kafka import KafkaConsumer, KafkaProducer
# Importa as exceções nativas do cliente Kafka
from kafka.errors import KafkaError
# Importa o construtor text do SQLAlchemy para escrita de instruções SQL puras
from sqlalchemy import text

# Importa as configurações globais centralizadas da aplicação CineLake
from cinelake.config import settings
# Importa a função get_engine para obter conexão com o banco de dados PostgreSQL
from cinelake.db import get_engine

# Instancia o logger com o nome do módulo corrente
logger = logging.getLogger(__name__)

# Nome do tópico principal do Kafka para consumo de eventos
TOPIC_PRINCIPAL = "movie-events"
# Nome do tópico secundário (Dead Letter Queue - DLQ) para mensagens corrompidas ou inválidas
TOPIC_DLQ = "movie-events-dlq"


# Função de validação para checar os campos obrigatórios e tipos de dados do evento
def validar_evento(evento: dict) -> bool:
    """Valida campos obrigatórios do evento."""
    # Verifica se o campo event_id está presente e não é uma string vazia
    if "event_id" not in evento or not evento["event_id"]:
        return False
    # Verifica se o tipo de evento está presente e não é vazio
    if "event_type" not in evento or not evento["event_type"]:
        return False
    # Verifica se o user_id está presente e é do tipo numérico inteiro (int)
    if "user_id" not in evento or not isinstance(evento["user_id"], int):
        return False
    # Verifica se o movie_id está presente e é do tipo numérico inteiro (int)
    if "movie_id" not in evento or not isinstance(evento["movie_id"], int):
        return False
    # Verifica se a propriedade com a data/hora original do evento está presente
    if "event_timestamp" not in evento:
        return False
    # Retorna True indicando que a validação do schema passou com sucesso
    return True


# Função responsável por salvar os eventos válidos no banco de dados PostgreSQL
def processar_evento(evento: dict) -> bool:
    """Insere evento válido na tabela event_log."""
    # Obtém o Engine de conexão com o banco de dados
    engine = get_engine()
    # Bloco de tratamento de exceção para a transação SQL
    try:
        # Abre o contexto de conexão com transação automatizada (commit automático ao final)
        with engine.begin() as conn:
            # Executa o comando SQL de inserção na tabela event_log com tratamento de chave primária duplicada
            conn.execute(
                text("""
                    INSERT INTO event_log (event_id, event_type, user_id, movie_id, payload, event_timestamp)
                    VALUES (:event_id, :event_type, :user_id, :movie_id, :payload, :event_timestamp)
                    ON CONFLICT (event_id) DO NOTHING
                """),
                {
                    # Passa o UUID do evento
                    "event_id": evento["event_id"],
                    # Passa a categoria do evento
                    "event_type": evento["event_type"],
                    # Passa o ID do usuário
                    "user_id": evento.get("user_id"),
                    # Passa o ID do filme
                    "movie_id": evento.get("movie_id"),
                    # Serializa todo o dicionário do evento como JSON para a coluna payload JSONB
                    "payload": json.dumps(evento),
                    # Converte o timestamp ISO para objeto datetime nativo com timezone
                    "event_timestamp": datetime.fromisoformat(evento["event_timestamp"]),
                },
            )
        # Retorna True sinalizando o sucesso do processamento e gravação
        return True
    # Captura falha na inserção no banco de dados
    except Exception as exc:
        # Registra no log o erro detalhado junto com a identificação do evento
        logger.error("Erro ao inserir evento %s: %s", evento.get("event_id"), exc)
        # Retorna False sinalizando a falha no processamento
        return False


# Função utilitária para redirecionar mensagens com falha ou inválidas para o tópico de DLQ
def enviar_para_dlq(evento: dict, motivo: str) -> None:
    """Envia evento inválido para a DLQ."""
    # Instancia um produtor temporário do Kafka para o envio da mensagem de erro
    produtor = KafkaProducer(
        # Passa o endereço dos servidores bootstrap do Kafka
        bootstrap_servers=settings.kafka_bootstrap_servers,
        # Serializa os dados da DLQ em bytes JSON
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    # Monta a estrutura da mensagem enriquecida com o motivo do erro e timestamp
    evento_dlq = {
        # O evento original que falhou
        "original_event": evento,
        # Motivo detalhado do erro ou reprovação na validação
        "error_reason": motivo,
        # Timestamp do momento do redirecionamento para a DLQ em UTC
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Dispara a mensagem para o tópico TOPIC_DLQ
    produtor.send(TOPIC_DLQ, value=evento_dlq)
    # Garante a descarga da mensagem no broker
    produtor.flush()
    # Fecha a conexão do produtor
    produtor.close()
    # Registra no log a transferência da mensagem para a fila de mensagens mortas (DLQ)
    logger.info("Evento enviado para DLQ: %s", evento.get("event_id"))


# Função principal para escutar o tópico do Kafka, validar schemas e processar as mensagens recebidas
def consumir_eventos(max_mensagens: int = 100, timeout_segundos: int = 10) -> None:
    """
    Consome eventos do tópico principal, valida e processa.

    Args:
        max_mensagens: número máximo de mensagens a processar.
        timeout_segundos: tempo de espera por novas mensagens.
    """
    # Instancia e inicializa o consumidor do Kafka
    consumidor = KafkaConsumer(
        # Nome do tópico principal configurado para ser escutado
        TOPIC_PRINCIPAL,
        # Endereço dos brokers do Kafka
        bootstrap_servers=settings.kafka_bootstrap_servers,
        # Lê a partir da mensagem mais antiga caso o grupo ainda não possua offset gravado
        auto_offset_reset="earliest",
        # Desativa o commit automático de offsets para controle manual estrito após processamento
        enable_auto_commit=False,
        # Nome do grupo de consumidores (Consumer Group) para balancamento de carga
        group_id="cinelake-consumer",
        # Função para desserializar os bytes JSON recebidos de volta em dicionário Python
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    # Contador de mensagens processadas com sucesso
    processados = 0
    # Bloco try para capturar interrupções e garantir fechamento limpo do cliente Kafka
    try:
        # Loop de consumo iterando sobre cada mensagem entregue pelo broker
        for mensagem in consumidor:
            # Extrai o dicionário deserializado do payload da mensagem
            evento = mensagem.value
            # Registra no log a recepção do evento
            logger.info("Recebido: %s", evento.get("event_id"))

            # Executa a checagem de schema e regras de validação
            if validar_evento(evento):
                # Processa e tenta gravar o evento no banco de dados
                sucesso = processar_evento(evento)
                # Se gravou no banco com sucesso
                if sucesso:
                    # Incrementa a contagem de mensagens processadas
                    processados += 1
                else:
                    # Caso ocorra falha de banco, envia para a Dead Letter Queue (DLQ)
                    enviar_para_dlq(evento, "erro_no_banco")
            else:
                # Se a validação de schema falhar, envia para a Dead Letter Queue (DLQ)
                enviar_para_dlq(evento, "validacao_falhou")

            # Executa o commit manual do offset da mensagem atual no Kafka
            consumidor.commit()

            # Interrompe a execução caso atinja o limite máximo de mensagens solicitado
            if processados >= max_mensagens:
                break

    # Captura a interrupção manual da execução (Ctrl+C no terminal)
    except KeyboardInterrupt:
        # Registra no log o encerramento manual
        logger.info("Interrompido pelo usuário")
    # Bloco finalizador sempre executado ao encerrar o consumidor
    finally:
        # Fecha o cliente do consumidor liberando recursos do cluster
        consumidor.close()

    # Registra no log a quantidade final de mensagens processadas
    logger.info("Consumo concluído. Eventos processados: %d", processados)
