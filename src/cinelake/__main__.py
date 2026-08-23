"""Ponto de entrada da CLI para o CineLake AI."""

import argparse
import logging
from pathlib import Path

from cinelake.config import settings
from cinelake.db import check_database_connection
from cinelake.ingestion.movielens.ingest import ingerir_movielens
from cinelake.ingestion.tmdb.ingest import ingerir_tmdb
from cinelake.logging_config import setup_logging


def main() -> None:
    """Executa um teste básico ('smoke test') e inicializa o CineLake AI."""
    # Configura o nível de logs com base nas configurações (ex: INFO, DEBUG, WARN)
    setup_logging(settings.log_level)

    # Configura o analisador de argumentos passados via terminal
    parser = argparse.ArgumentParser(description="CineLake AI CLI")

    # Adiciona subparsers para suporte a subcomandos organizados
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Subcomando 'check-db' para testar conexão com o banco
    subparsers.add_parser("check-db", help="Verifica a conexão com o banco de dados")

    # Subcomando 'ingest-movielens' para iniciar a ingestão do MovieLens
    parser_ingest = subparsers.add_parser("ingest-movielens", help="Executa a ingestão do MovieLens")
    parser_ingest.add_argument(
        "--data-dir",
        required=True,
        help="Caminho para o diretório contendo os CSVs do MovieLens",
    )

    # Subcomando 'ingest-tmdb' para iniciar a ingestão do TMDb
    parser_tmdb = subparsers.add_parser("ingest-tmdb", help="Executa a ingestão incremental do TMDb")
    parser_tmdb.add_argument(
        "--output-dir",
        default="data/raw/tmdb",
        help="Caminho para salvar os JSONs brutos do TMDb (padrão: data/raw/tmdb)",
    )
    parser_tmdb.add_argument(
        "--rps",
        type=float,
        default=4.0,
        help="Requisições por segundo para rate limit (padrão: 4.0)",
    )
    parser_tmdb.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite de filmes para processar nesta execução (opcional)",
    )

    # Mantém compatibilidade legada com a flag '--check-db' antiga
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Check database connectivity (legado)",
    )
    args = parser.parse_args()

    # Obtém a instância do logger para este arquivo
    logger = logging.getLogger(__name__)
    logger.info(
        "CineLake AI initialized",
        extra={"environment": settings.environment},
    )

    # Lógica de decisão baseada nos comandos/flags informados
    if args.command == "check-db" or args.check_db:
        logger.info("Checking database connection...")
        ok = check_database_connection()
        if ok:
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
            # Encerra o script com código de erro 1 se a conexão falhar
            raise SystemExit(1)

    elif args.command == "ingest-movielens":
        logger.info("Starting MovieLens ingestion via CLI...")
        diretorio = Path(args.data_dir)
        if not diretorio.exists():
            logger.error("Directory not found: %s", diretorio)
            raise SystemExit(1)
        try:
            resultado = ingerir_movielens(diretorio)
            logger.info("Ingestion completed: %s", resultado)
        except Exception as exc:
            logger.error("Ingestion failed: %s", exc)
            raise SystemExit(1) from exc

    elif args.command == "ingest-tmdb":
        logger.info("Starting TMDb ingestion via CLI...")
        diretorio_saida = Path(args.output_dir)
        try:
            resultado_tmdb = ingerir_tmdb(
                diretorio_saida=diretorio_saida,
                requests_per_second=args.rps,
                max_filmes_por_execucao=args.limit,
            )
            logger.info("TMDb Ingestion completed: %s", resultado_tmdb)
        except Exception as exc:
            logger.error("TMDb Ingestion failed: %s", exc)
            raise SystemExit(1) from exc

    else:
        # Se nenhum argumento ou comando válido for fornecido, exibe a ajuda da CLI
        parser.print_help()


# Garante que o método main() só roda se o arquivo for executado diretamente (ex: python -m cinelake)
if __name__ == "__main__":
    main()
