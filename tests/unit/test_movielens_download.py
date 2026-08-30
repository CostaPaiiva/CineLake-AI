"""Testes para as funções de download e extração do MovieLens."""

import zipfile
from pathlib import Path

# Importa a função de extração que será testada
from cinelake.ingestion.movielens.download import extrair_zip


def test_extrair_zip(tmp_path: Path) -> None:
    """Deve extrair corretamente um arquivo ZIP com conteúdo."""
    # 1. Preparação (Setup)
    # Define o caminho do arquivo ZIP de teste dentro da pasta temporária fornecida pelo Pytest (tmp_path)
    arquivo_zip = tmp_path / "teste.zip"

    # Cria o arquivo ZIP temporário e escreve um arquivo de texto de teste lá dentro
    with zipfile.ZipFile(arquivo_zip, "w") as zip_ref:
        zip_ref.writestr("arquivo_teste.txt", "conteúdo")

    # Define a pasta onde os arquivos do zip devem ser extraídos
    destino = tmp_path / "extraido"

    # 2. Execução (Action)
    # Chama a função sendo testada para extrair o ZIP temporário
    extrair_zip(arquivo_zip, destino)

    # 3. Verificação (Assert)
    # Verifica se o arquivo interno do ZIP foi criado fisicamente no destino
    assert (destino / "arquivo_teste.txt").exists()

    # Verifica se o conteúdo do arquivo extraído é exatamente o que colocamos nele
    assert (destino / "arquivo_teste.txt").read_text(encoding="utf-8") == "conteúdo"
