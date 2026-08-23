"""Ponto de entrada da Interface de Linha de Comando (CLI) do CineLake AI."""

import argparse
import logging
from pathlib import Path

from cinelake.config import settings
from cinelake.db import check_database_connection
from cinelake.logging_config import setup_logging


def main() -> None:
    """Configura o analisador de argumentos e dispara o comando solicitado na CLI."""
    # Configura os formatos e níveis de log centralizados da aplicação
    setup_logging(settings.log_level)

    # Cria o parser principal da CLI
    parser = argparse.ArgumentParser(description="CineLake AI CLI")
    # Subparsers para gerenciar os subcomandos disponíveis no projeto
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # 1. Subcomando: check-db (Validação de conectividade com o banco)
    parser_check = subparsers.add_parser(
        "check-db",
        help="Verifica conexão com o banco de dados PostgreSQL",
    )
    parser_check.set_defaults(func=_cmd_check_db)

    # 2. Subcomando: ingest-movielens (Ingestão em lote dos CSVs do MovieLens)
    parser_ingest_ml = subparsers.add_parser(
        "ingest-movielens",
        help="Ingere os arquivos CSV do MovieLens no PostgreSQL",
    )
    parser_ingest_ml.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/raw/movielens/ml-latest-small"),
        help="Diretório contendo os CSVs extraídos (padrão: data/raw/movielens/ml-latest-small)",
    )
    parser_ingest_ml.set_defaults(func=_cmd_ingest_movielens)

    # 3. Subcomando: ingest-tmdb (Ingestão incremental da API do TMDb)
    parser_ingest_tmdb = subparsers.add_parser(
        "ingest-tmdb",
        help="Ingere metadados incrementais do catálogo TMDB",
    )
    parser_ingest_tmdb.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/tmdb"),
        help="Diretório onde os arquivos JSON brutos serão salvos (padrão: data/raw/tmdb)",
    )
    parser_ingest_tmdb.add_argument(
        "--max-filmes",
        "--limit",
        type=int,
        default=None,
        dest="max_filmes",
        help="Limite opcional de filmes a processar nesta rodada",
    )
    parser_ingest_tmdb.set_defaults(func=_cmd_ingest_tmdb)

    # Processa os argumentos fornecidos pelo usuário no terminal
    args = parser.parse_args()
    # Executa a função vinculada ao subcomando escolhido
    args.func(args)


def _cmd_check_db(args: argparse.Namespace) -> None:
    """Executa a verificação de saúde da conexão com o PostgreSQL."""
    logger = logging.getLogger(__name__)
    logger.info("Verificando conexão com o banco de dados...")
    if check_database_connection():
        logger.info("Conexão com o banco de dados bem-sucedida")
    else:
        logger.error("Falha na conexão com o banco de dados")
        # Encerra a execução com código de saída 1 (erro)
        raise SystemExit(1)


def _cmd_ingest_movielens(args: argparse.Namespace) -> None:
    """Dispara o pipeline de ingestão do dataset MovieLens."""
    # Import tardio para otimizar tempo de inicialização da CLI
    from cinelake.ingestion.movielens.ingest import ingerir_movielens

    logger = logging.getLogger(__name__)
    logger.info("Iniciando ingestão do MovieLens a partir de %s...", args.data_dir)
    resultado = ingerir_movielens(args.data_dir)
    logger.info("Ingestão do MovieLens finalizada com sucesso: %s", resultado)


def _cmd_ingest_tmdb(args: argparse.Namespace) -> None:
    """Dispara o pipeline de ingestão incremental de metadados do TMDb."""
    # Import tardio para otimizar tempo de inicialização da CLI
    from cinelake.ingestion.tmdb.ingest import ingerir_tmdb

    logger = logging.getLogger(__name__)
    logger.info("Iniciando ingestão incremental do TMDb...")
    resultado = ingerir_tmdb(
        diretorio_saida=args.output_dir,
        max_filmes_por_execucao=args.max_filmes,
    )
    logger.info("Ingestão do TMDb finalizada com sucesso: %s", resultado)


# Ponto de entrada padrão para execução via módulo (ex: python -m cinelake)
if __name__ == "__main__":
    main()
