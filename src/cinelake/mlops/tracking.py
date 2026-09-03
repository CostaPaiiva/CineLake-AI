# Módulo contendo funções utilitárias para configuração e rastreamento de experimentos com o MLflow
"""Funções auxiliares para tracking com MLflow."""

# Importação da biblioteca padrão de manipulação de logs do Python
import logging
# Importação do módulo os da biblioteca padrão para manipulação de variáveis de ambiente
import os
# Importação da classe Path da biblioteca padrão pathlib para tratamento de caminhos de arquivos e diretórios
from pathlib import Path

# Importação da biblioteca principal do MLflow para rastreamento de experimentos e modelos
import mlflow
# Importação do cliente MlflowClient para interação direta com a API do servidor de experimentos do MLflow
from mlflow.tracking import MlflowClient

# Inicialização do logger específico para este módulo MLOps
logger = logging.getLogger(__name__)


# Função responsável por configurar as variáveis de ambiente necessárias para comunicação entre o MLflow e o MinIO (S3)
def configurar_tracking() -> None:
    """Configura as variáveis de ambiente para o MLflow e MinIO."""
    # Carrega as configurações centralizadas da aplicação CineLake AI
    from cinelake.config import settings

    # Define a variável de ambiente do URI de rastreamento do MLflow caso ainda não esteja configurada no ambiente
    os.environ.setdefault("MLFLOW_TRACKING_URI", settings.mlflow_tracking_uri)
    # Define a chave de acesso (usuário) do S3/MinIO necessária para upload de artefatos
    os.environ.setdefault("AWS_ACCESS_KEY_ID", settings.minio_access_key)
    # Define a chave secreta (senha) do S3/MinIO necessária para upload de artefatos
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", settings.minio_secret_key)
    # Define a URL do endpoint do S3/MinIO para onde os artefatos serão enviados
    os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", settings.mlflow_s3_endpoint_url)
    # Define a flag de desativação de checagem SSL/TLS convertida para formato string em letras minúsculas ("true"/"false")
    os.environ.setdefault("MLFLOW_S3_IGNORE_TLS", str(settings.mlflow_s3_ignore_tls).lower())

    # Configura explicitamente o URI de rastreamento no cliente global do MLflow
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    # Registra no log de informação o URI de rastreamento atualmente ativo no MLflow
    logger.info("Tracking URI: %s", mlflow.get_tracking_uri())


# Função utilitária para buscar um experimento existente pelo nome ou criar um novo caso não exista
def get_ou_criar_experimento(nome: str) -> str:
    """Retorna o ID do experimento, criando-o se não existir."""
    # Instancia o cliente da API do MLflow
    cliente = MlflowClient()
    # Busca um experimento cadastrado no MLflow com o nome especificado
    experimento = cliente.get_experiment_by_name(nome)
    # Verifica se o experimento não foi encontrado no banco de dados do MLflow
    if experimento is None:
        # Cria um novo experimento com o nome fornecido e obtém o ID gerado pelo MLflow
        experiment_id = cliente.create_experiment(nome)
        # Registra no log de informação a criação com sucesso do novo experimento e seu ID
        logger.info("Experimento %s criado com ID %s", nome, experiment_id)
        # Retorna o ID do novo experimento recém-criado
        return experiment_id
    # Retorna o ID do experimento já existente no MLflow
    return experimento.experiment_id


# Função principal para registrar os dados de uma execução (run) de treino ou avaliação de modelo no MLflow
def log_parametros_e_metricas(
    experimento_nome: str, # Nome do experimento no qual a execução será registrada
    parametros: dict, # Dicionário contendo os hiperparâmetros e configurações da execução
    metricas: dict, # Dicionário contendo os resultados das métricas de desempenho avaliadas
    artefato_dir: Path | None = None, # Caminho opcional do diretório local contendo arquivos de artefatos para upload
) -> None:
    """
    Registra uma execução no MLflow com parâmetros, métricas e artefatos.

    Args:
        experimento_nome: Nome do experimento.
        parametros: Dicionário de parâmetros.
        metricas: Dicionário de métricas.
        artefato_dir: Diretório com artefatos (opcional).
    """
    # Garante que as configurações de tracking e credenciais do S3/MinIO foram inicializadas
    configurar_tracking()
    # Obtém o ID do experimento existente ou cria um novo para vincular esta execução
    experiment_id = get_ou_criar_experimento(experimento_nome)

    # Inicia um novo contexto de execução (run) associado ao ID do experimento obtido
    with mlflow.start_run(experiment_id=experiment_id) as run:
        # Itera sobre cada parâmetro presente no dicionário de parâmetros fornecido
        for chave, valor in parametros.items():
            # Registra o par chave/valor do parâmetro no contexto do run atual do MLflow
            mlflow.log_param(chave, valor)

        # Itera sobre cada métrica presente no dicionário de métricas fornecido
        for chave, valor in metricas.items():
            # Registra o par chave/valor da métrica numérica no contexto do run atual do MLflow
            mlflow.log_metric(chave, valor)

        # Checa se o diretório de artefatos foi informado e se ele realmente existe no sistema de arquivos
        if artefato_dir and artefato_dir.exists():
            # Faz o upload de todos os arquivos do diretório para o armazenamento de artefatos (MinIO S3) do MLflow
            mlflow.log_artifacts(str(artefato_dir))

        # Registra no log de informação que a execução foi registrada com sucesso, exibindo seu ID exclusivo (run_id)
        logger.info("Run registrado: %s", run.info.run_id)
