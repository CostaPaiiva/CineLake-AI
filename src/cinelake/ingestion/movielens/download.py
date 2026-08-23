"""Funções para baixar e extrair o dataset MovieLens."""

import logging
from pathlib import Path
import urllib.request
import zipfile

# Configuração do logger local para registrar o progresso das operações
logger = logging.getLogger(__name__)

# URL padrão para download do conjunto de dados reduzido (small) do MovieLens
URL_MOVIELENS_PEQUENO = (
    "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
)


def baixar_movielens(url: str, destino: Path) -> Path:
    """Baixa o arquivo ZIP do MovieLens e retorna o caminho do arquivo.
    
    Args:
        url: Link direto para download do dataset (.zip)
        destino: Diretório local onde o arquivo zip será salvo
        
    Returns:
        Caminho absoluto do arquivo ZIP baixado
    """
    # Garante que as pastas de destino existam
    destino.mkdir(parents=True, exist_ok=True)
    caminho_zip = destino / "ml-latest-small.zip"

    # Evita baixar o arquivo novamente se ele já existir localmente
    if caminho_zip.exists():
        logger.info("Arquivo ZIP já existe: %s", caminho_zip)
        return caminho_zip

    # Efetua a requisição HTTP e faz o download do arquivo
    logger.info("Baixando %s para %s", url, caminho_zip)
    urllib.request.urlretrieve(url, caminho_zip)
    logger.info("Download concluído: %s", caminho_zip)
    return caminho_zip


def extrair_zip(caminho_zip: Path, destino: Path) -> None:
    """Extrai o conteúdo do ZIP para a pasta de destino.
    
    Args:
        caminho_zip: Caminho do arquivo ZIP de origem
        destino: Pasta onde os arquivos extraídos serão salvos
    """
    # Garante que a pasta para extração exista
    destino.mkdir(parents=True, exist_ok=True)
    logger.info("Extraindo %s para %s", caminho_zip, destino)

    # Abre e extrai recursivamente todos os arquivos contidos no ZIP
    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(destino)

    logger.info("Extração concluída em %s", destino)