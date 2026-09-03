# Módulo produtor responsável por gerar e disparar eventos simulados de interação para o tópico do Kafka
"""Produtor de eventos simulados para Kafka."""

# Importa a biblioteca json nativa para serialização de eventos no formato JSON
import json
# Importa a biblioteca de logging para diagnóstico e log de operações
import logging
# Importa o módulo time para gerenciamento de intervalos entre envios de mensagens
import time
# Importa a biblioteca uuid para geração de identificadores únicos universais de eventos
import uuid
# Importa datetime e timezone para timestamp padronizado com fuso horário UTC
from datetime import datetime, timezone

# Importa o produtor oficial da biblioteca kafka-python
from kafka import KafkaProducer
# Importa o tratamento de erros do cliente Kafka
from kafka.errors import KafkaError

# Importa as configurações globais da aplicação CineLake
from cinelake.config import settings

# Instancia o logger com o nome do próprio módulo
logger = logging.getLogger(__name__)

# Nome padrão do tópico principal do Kafka para publicação de eventos de filmes
TOPIC_PRINCIPAL = "movie-events"


# Função responsável por criar e configurar uma instância do produtor Kafka
def criar_produtor() -> KafkaProducer:
    """Cria e retorna um produtor Kafka."""
    # Instancia o KafkaProducer configurando o servidor de bootstrap e serializadores de dados
    produtor = KafkaProducer(
        # Especifica os endereços de bootstrap servers do Kafka obtidos via arquivo de configuração
        bootstrap_servers=settings.kafka_bootstrap_servers,
        # Define a função lambda de serialização dos valores de dicionário para bytes codificados em UTF-8
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        # Define a função lambda de serialização das chaves de mensagem para bytes codificados em UTF-8
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    # Registra no log a criação bem sucedida do produtor informando os servidores configurados
    logger.info("Produtor Kafka criado para %s", settings.kafka_bootstrap_servers)
    # Retorna a instância ativa do KafkaProducer
    return produtor


# Função para gerar um evento sintético/aleatório de interação de usuário com o catálogo de filmes
def gerar_evento_aleatorio() -> dict:
    """Gera um evento de interação de filme."""
    # Importa o módulo random nativo para escolha aleatória de eventos e valores
    import random

    # Lista dos tipos de eventos de interação suportados pela aplicação
    tipos_eventos = [
        "movie_view",
        "movie_click",
        "movie_rating",
        "movie_favorite",
        "search",
        "recommendation_view",
        "recommendation_click",
    ]
    # Constrói o dicionário representando o schema do evento
    evento = {
        # Gera uma chave UUID v4 no formato string como identificador único do evento
        "event_id": str(uuid.uuid4()),
        # Seleciona aleatoriamente um dos tipos de eventos da lista
        "event_type": random.choice(tipos_eventos),
        # Simula o ID de um usuário sorteando um número inteiro entre 1 e 600
        "user_id": random.randint(1, 600),
        # Simula o ID de um filme sorteando um número inteiro entre 1 e 9000
        "movie_id": random.randint(1, 9000),
        # Registra a data/hora atual no padrão ISO-8601 em fuso horário UTC
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Se o tipo do evento for uma avaliação ("movie_rating"), adiciona a nota atribuída
    if evento["event_type"] == "movie_rating":
        # Sorteia uma nota inteira entre 1 e 5 estrelas
        evento["rating"] = random.randint(1, 5)
    # Retorna o dicionário populado com o evento gerado
    return evento


# Função pública para produzir e enviar uma sequência de eventos sintéticos para o Kafka
def produzir_eventos(quantidade: int = 10, intervalo_segundos: float = 0.0) -> None:
    """
    Produz uma quantidade determinada de eventos para o tópico.

    Args:
        quantidade: número de eventos a produzir.
        intervalo_segundos: intervalo entre eventos.
    """
    # Inicializa o produtor Kafka
    produtor = criar_produtor()
    # Executa o loop de produção para a quantidade de mensagens especificada
    for i in range(quantidade):
        # Gera o dicionário de evento aleatório
        evento = gerar_evento_aleatorio()
        # Define o ID do usuário como chave para distribuição equilibrada nas partições do tópico
        chave = str(evento.get("user_id", "unknown"))
        # Dispara o envio assíncrono do evento para o tópico principal do Kafka
        futuro = produtor.send(TOPIC_PRINCIPAL, key=chave, value=evento)
        # Tenta aguardar a confirmação de recebimento pelo broker (com timeout de 10 segundos)
        try:
            # Bloqueia até a resposta do broker ou até estourar o timeout
            futuro.get(timeout=10)
            # Registra no log de informação o envio confirmado do evento
            logger.info("Evento enviado: %s", evento["event_id"])
        # Trata exceção de falha de transmissão do Kafka
        except KafkaError as exc:
            # Registra a falha no log de erro
            logger.error("Erro ao enviar evento: %s", exc)
        # Se um intervalo de tempo positivo foi especificado entre envios
        if intervalo_segundos > 0:
            # Pausa a execução pelo número de segundos configurado
            time.sleep(intervalo_segundos)
    # Garante o envio de todas as mensagens pendentes no buffer do cliente
    produtor.flush()
    # Fecha a conexão do produtor com os brokers do Kafka
    produtor.close()
    # Registra no log a conclusão do lote de mensagens
    logger.info("Produção concluída: %d eventos", quantidade)
