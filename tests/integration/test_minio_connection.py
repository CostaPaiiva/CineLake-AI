"""Teste de integração para verificar a conectividade e operações básicas no MinIO."""

import pytest

from cinelake.config import settings
from cinelake.datalake.minio_client import criar_cliente_minio, garantir_bucket


@pytest.mark.integration
def test_conexao_minio():
    """Testa se a conexão com o MinIO está ativa e se o bucket padrão foi criado."""
    # Instancia o cliente do MinIO utilizando as configurações ativas do ambiente
    cliente = criar_cliente_minio()

    # Assegura que o bucket de testes/desenvolvimento (ex: data-lake) esteja criado no MinIO
    garantir_bucket(cliente, settings.minio_bucket)

    # Lista todos os buckets atualmente existentes no servidor MinIO
    resposta = cliente.list_buckets()

    # Extrai apenas os nomes dos buckets da resposta da API
    nomes = [b["Name"] for b in resposta["Buckets"]]

    # Valida se o bucket padrão configurado está presente na lista de buckets do MinIO
    assert settings.minio_bucket in nomes
