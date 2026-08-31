"""Ponto de entrada da Interface de Linha de Comando (CLI) do CineLake AI."""

import argparse  # Importa o módulo nativo para análise de argumentos de linha de comando.
import logging  # Importa o módulo nativo para registro e formatação de logs.
from pathlib import Path  # Importa a classe Path para manipulação orientada a objetos de caminhos no sistema de arquivos.

from cinelake.config import settings  # Importa as configurações globais da aplicação.
from cinelake.db import check_database_connection  # Importa a função de verificação de integridade da conexão com o banco.
from cinelake.logging_config import setup_logging  # Importa a função de inicialização e configuração centralizada de logs.


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

    # 4. Subcomando: ingest-datalake-bronze (Ingestão de dados brutos no Data Lake bronze)
    parser_bronze = subparsers.add_parser(
        "ingest-datalake-bronze", help="Ingere dados brutos no Data Lake bronze"
    )
    parser_bronze.add_argument(
        "--movielens-dir",
        type=Path,
        default=Path("data/raw/movielens/ml-latest-small"),
        help="Diretório com CSVs do MovieLens",
    )
    parser_bronze.add_argument(
        "--tmdb-dir",
        type=Path,
        default=Path("data/raw/tmdb"),
        help="Diretório com JSONs do TMDB",
    )
    parser_bronze.set_defaults(func=_cmd_ingest_bronze)

    # 5. Subcomando: run-metrics-exporter (Inicia o servidor de métricas Prometheus)
    parser_metrics = subparsers.add_parser(
        "run-metrics-exporter", help="Inicia exporter de métricas Prometheus"
    )
    parser_metrics.add_argument("--port", type=int, default=8000, help="Porta do exporter")
    parser_metrics.set_defaults(func=_cmd_run_metrics_exporter)

    # 6. Subcomando: serve-observability (Sobe API de observabilidade com FastAPI e Uvicorn)
    parser_obs = subparsers.add_parser("serve-observability", help="Sobe API de observabilidade")
    parser_obs.add_argument(
        "--host", type=str, default="127.0.0.1", help="Endereço IP para bind do servidor"
    )
    parser_obs.add_argument(
        "--port", type=int, default=8000, help="Porta TCP para bind do servidor"
    )
    parser_obs.set_defaults(func=_cmd_serve_obs)

    # 7. Subcomando: collect-rag-documents (Coleta e normaliza documentos de contexto para o RAG)
    parser_rag = subparsers.add_parser("collect-rag-documents", help="Coleta documentos para RAG")
    parser_rag.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/rag/documents"),
        help="Diretório para salvar documentos normalizados (padrão: data/rag/documents)",
    )
    parser_rag.set_defaults(func=_cmd_collect_rag)

    # 8. Subcomando: index-rag-documents (Indexa documentos RAG e gera embeddings no pgvector)
    parser_index = subparsers.add_parser(
        "index-rag-documents", help="Indexa documentos RAG no pgvector"
    )
    parser_index.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/rag/documents"),
        help="Diretório com os documentos JSON",
    )
    parser_index.set_defaults(func=_cmd_index_rag)

    # 9. Subcomando: serve-rag-mcp (Sobe API FastAPI que combina RAG e MCP)
    parser_rag_mcp = subparsers.add_parser("serve-rag-mcp", help="Sobe API RAG+MCP")
    # Define o argumento de endereço IP/host para bind do servidor (padrão: 127.0.0.1)
    parser_rag_mcp.add_argument("--host", type=str, default="127.0.0.1", help="Host")
    # Define o argumento de porta TCP para bind do servidor (padrão: 8001)
    parser_rag_mcp.add_argument("--port", type=int, default=8001, help="Porta")
    # Vincula o subcomando à função correspondente que executa o servidor
    parser_rag_mcp.set_defaults(func=_cmd_serve_rag_mcp)

    # 10. Subcomando: evaluate-rag (Avalia o sistema RAG usando dataset de teste)
    parser_eval = subparsers.add_parser("evaluate-rag", help="Avalia o sistema RAG")
    # Argumento do caminho para o dataset JSON de avaliação
    parser_eval.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/rag/evaluation/eval_dataset.json"),
        help="Caminho para o dataset de avaliação",
    )
    # Argumento para quantidade de documentos top-k a considerar na avaliação
    parser_eval.add_argument(
        "--k", type=int, default=5, help="Número de documentos top-k"
    )
    # Vincula o subcomando à função de execução do evaluate-rag
    parser_eval.set_defaults(func=_cmd_evaluate_rag)

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


def _cmd_ingest_bronze(args: argparse.Namespace) -> None:
    """Executa a ingestão da camada bronze do Data Lake."""
    from cinelake.datalake.bronze_ingest import ingerir_bronze

    logger = logging.getLogger(__name__)
    logger.info("Iniciando ingestão bronze...")
    resultado = ingerir_bronze(args.movielens_dir, args.tmdb_dir)
    logger.info("Resultado: %s", resultado)


def _cmd_run_metrics_exporter(args: argparse.Namespace) -> None:
    """Inicia o servidor de exportação de métricas HTTP do Prometheus."""
    import time

    from prometheus_client import start_http_server

    logger = logging.getLogger(__name__)
    # Inicializa o servidor HTTP interno na porta especificada (padrão 8000)
    start_http_server(args.port)
    logger.info("Exporter de métricas rodando na porta %s", args.port)
    # Loop infinito mantendo o processo ativo para responder a raspagens (scrapes) do Prometheus
    while True:
        time.sleep(10)


def _cmd_serve_obs(args: argparse.Namespace) -> None:
    """Inicia o servidor web ASGI Uvicorn executando a API FastAPI de observabilidade."""
    import uvicorn

    from cinelake.observability.api import app

    logger = logging.getLogger(__name__)
    logger.info("Iniciando API de observabilidade em %s:%s", args.host, args.port)
    # Executa o servidor ASGI apontando para a aplicação FastAPI
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def _cmd_collect_rag(args: argparse.Namespace) -> None:
    """Executa a coleta e normalização de documentos de contexto para o pipeline de RAG."""
    from cinelake.rag.collector import coletar_documentos_rag

    logger = logging.getLogger(__name__)
    logger.info("Iniciando coleta de documentos RAG...")
    resultado = coletar_documentos_rag(args.output_dir)
    logger.info("Resultado: %s", resultado)


def _cmd_index_rag(args: argparse.Namespace) -> None:
    """Executa a indexação e vetorização dos documentos RAG no PostgreSQL (pgvector)."""
    from cinelake.rag.indexer import indexar_documentos

    logger = logging.getLogger(__name__)
    logger.info("Iniciando indexação RAG...")
    resultado = indexar_documentos(args.input_dir)
    logger.info("Resultado: %s", resultado)


def _cmd_serve_rag_mcp(args: argparse.Namespace) -> None:
    # Docstring da função explicitando que inicia o servidor FastAPI para RAG+MCP.
    """Inicia o servidor FastAPI para RAG+MCP."""
    # Importação tardia do servidor Uvicorn para hospedagem ASGI da aplicação web.
    import uvicorn

    # Importação tardia da aplicação FastAPI do módulo rag_mcp.
    from cinelake.api.rag_mcp import app

    # Obtém a instância do logger para este módulo.
    logger = logging.getLogger(__name__)
    # Registra no log o início da execução da API informando host e porta.
    logger.info("Iniciando API RAG+MCP em %s:%s", args.host, args.port)
    # Inicializa o servidor ASGI uvicorn passando a instância da aplicação FastAPI.
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def _cmd_evaluate_rag(args: argparse.Namespace) -> None:
    """Executa avaliação RAG."""
    from cinelake.rag.evaluate import avaliar_rag

    logger = logging.getLogger(__name__)
    logger.info("Iniciando avaliação RAG...")
    resultado = avaliar_rag(args.dataset, args.k)
    logger.info("Resultado: %s", resultado)


# Ponto de entrada padrão para execução via módulo (ex: python -m cinelake)
if __name__ == "__main__":
    main()
