"""Cliente para interagir com o MinIO através da biblioteca boto3 (S3 API)."""

import logging
from pathlib import Path

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from cinelake.config import settings

# Inicializa o logger para registrar eventos e erros deste módulo
logger = logging.getLogger(__name__)


def criar_cliente_minio() -> BaseClient:
    """Cria e retorna um cliente boto3 configurado para se conectar à API do MinIO.

    A conexão simula a API do Amazon S3 apontando para o endpoint do MinIO.
    """
    cliente = boto3.client(
        "s3",
        # URL do servidor MinIO montada a partir das configurações
        endpoint_url=f"http://{settings.minio_endpoint}",
        # Chaves de autenticação do MinIO
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        # Define a versão de assinatura do protocolo de segurança como s3v4
        config=Config(signature_version="s3v4"),
        # O MinIO local não exige região real, definimos um padrão compatível
        region_name="us-east-1",
    )
    logger.info("Cliente MinIO criado para %s", settings.minio_endpoint)
    return cliente


def garantir_bucket(cliente: BaseClient, bucket: str) -> None:
    """Verifica se um bucket (diretório raiz do S3) existe no MinIO e o cria caso não exista.

    Args:
        cliente: A instância de conexão ativa com o MinIO.
        bucket: Nome do bucket que deseja verificar ou criar.
    """
    try:
        # Tenta ler os metadados do bucket para testar se ele já existe
        cliente.head_bucket(Bucket=bucket)
        logger.info("Bucket %s já existe", bucket)
    except Exception:
        # Se a chamada acima falhar, significa que o bucket não existe, então nós o criamos
        logger.info("Criando bucket %s", bucket)
        cliente.create_bucket(Bucket=bucket)


def fazer_upload_parquet(
    cliente: BaseClient,
    bucket: str,
    chave: str,
    arquivo_local: Path,
) -> None:
    """Realiza o upload de um arquivo local (geralmente formato Parquet) para o MinIO.

    Args:
        cliente: A instância de conexão ativa com o MinIO.
        bucket: O nome do bucket de destino.
        chave: O caminho/nome virtual que o arquivo terá dentro do bucket (ex: raw/movies.parquet).
        arquivo_local: O caminho físico do arquivo local na máquina.
    """
    logger.info("Upload de %s para s3://%s/%s", arquivo_local, bucket, chave)
    # Executa o upload do arquivo convertendo o Path para string (exigência do boto3)
    cliente.upload_file(str(arquivo_local), bucket, chave)
