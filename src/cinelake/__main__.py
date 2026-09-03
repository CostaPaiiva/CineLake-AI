"""Ponto de entrada da Interface de Linha de Comando (CLI) do CineLake AI."""

import argparse  # Importa o módulo nativo para análise de argumentos de linha de comando.
import logging  # Importa o módulo nativo para registro e formatação de logs.
from pathlib import (
    Path,  # Importa a classe Path para manipulação orientada a objetos de caminhos no sistema de arquivos.
)

from cinelake.config import settings  # Importa as configurações globais da aplicação.
from cinelake.db import (
    check_database_connection,  # Importa a função de verificação de integridade da conexão com o banco.
)
from cinelake.logging_config import (
    setup_logging,  # Importa a função de inicialização e configuração centralizada de logs.
)


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

    # 11. Subcomando: train-popularity-model (Treina/calcula modelo de popularidade)
    parser_pop = subparsers.add_parser("train-popularity-model", help="Treina/calcula modelo de popularidade")
    # Vincula o subcomando à função de execução do treino de popularidade
    parser_pop.set_defaults(func=_cmd_train_popularity)

    # 12. Subcomando: generate-popular-recommendations (Gera recomendações populares)
    parser_rec = subparsers.add_parser("generate-popular-recommendations", help="Gera recomendações populares")
    # Adiciona argumento --top-n para definir o número de recomendações por usuário
    parser_rec.add_argument("--top-n", type=int, default=100, help="Número de recomendações por usuário")
    # Vincula o subcomando à função de geração de recomendações
    parser_rec.set_defaults(func=_cmd_generate_popular)

    # 13. Subcomando: train-content-based-model (Treina/calcula similaridade content-based)
    parser_cb = subparsers.add_parser("train-content-based-model", help="Treina/calcula similaridade content-based")
    # Vincula o subcomando à função de execução do treino content-based
    parser_cb.set_defaults(func=_cmd_train_content_based)

    # 14. Subcomando: generate-content-recommendations (Gera recomendações content-based)
    parser_gen_cb = subparsers.add_parser("generate-content-recommendations", help="Gera recomendações content-based")
    # Adiciona argumento --top-n para definir o número de recomendações por usuário
    parser_gen_cb.add_argument("--top-n", type=int, default=100, help="Número de recomendações por usuário")
    # Vincula o subcomando à função de geração de recomendações content-based
    parser_gen_cb.set_defaults(func=_cmd_generate_content_based)

    # 15. Subcomando: train-collaborative-model (Treina/calcula similaridade colaborativa)
    parser_cf = subparsers.add_parser("train-collaborative-model", help="Treina/calcula similaridade colaborativa")
    # Vincula o subcomando à função de execução do treino colaborativo
    parser_cf.set_defaults(func=_cmd_train_collaborative)

    # 16. Subcomando: generate-collaborative-recommendations (Gera recomendações colaborativas)
    parser_gen_cf = subparsers.add_parser("generate-collaborative-recommendations", help="Gera recomendações colaborativas")
    # Adiciona argumento --top-n para definir o número de recomendações por usuário
    parser_gen_cf.add_argument("--top-n", type=int, default=100, help="Número de recomendações por usuário")
    # Vincula o subcomando à função de geração de recomendações colaborativas
    parser_gen_cf.set_defaults(func=_cmd_generate_collaborative)

    # 17. Subcomando: generate-hybrid-recommendations (Gera recomendações híbridas)
    parser_gen_hy = subparsers.add_parser("generate-hybrid-recommendations", help="Gera recomendações híbridas")
    # Adiciona argumento --top-n para definir o número de recomendações por usuário
    parser_gen_hy.add_argument("--top-n", type=int, default=100, help="Número de recomendações por usuário")
    # Adiciona argumento --peso-content para o peso do modelo content-based
    parser_gen_hy.add_argument("--peso-content", type=float, default=0.4, help="Peso do content-based")
    # Adiciona argumento --peso-collab para o peso do modelo colaborativo
    parser_gen_hy.add_argument("--peso-collab", type=float, default=0.6, help="Peso do collaborative")
    # Vincula o subcomando à função de geração de recomendações híbridas
    parser_gen_hy.set_defaults(func=_cmd_generate_hybrid)

    # 18. Subcomando: evaluate-all-models (Avalia todos os modelos)
    parser_eval_models = subparsers.add_parser("evaluate-all-models", help="Avalia todos os modelos")
    # Adiciona argumento --top-k para definir o limite de corte na avaliação
    parser_eval_models.add_argument("--top-k", type=int, default=10, help="Top-K para avaliação")
    # Vincula o subcomando à função de avaliação de todos os modelos
    parser_eval_models.set_defaults(func=_cmd_evaluate_all_models)

    # 19. Subcomando: serve-main-api (Sobe a API principal com FastAPI e Uvicorn)
    parser_main = subparsers.add_parser("serve-main-api", help="Sobe a API principal")
    # Define o argumento de endereço IP/host para bind do servidor da API principal (padrão: 127.0.0.1)
    parser_main.add_argument("--host", type=str, default="127.0.0.1", help="Host")
    # Define o argumento de porta TCP para bind do servidor da API principal (padrão: 8002)
    parser_main.add_argument("--port", type=int, default=8002, help="Porta")
    # Vincula o subcomando à função que dispara a execução do servidor FastAPI principal
    parser_main.set_defaults(func=_cmd_serve_main)

    # 20. Subcomando: produce-events (Produz eventos de teste para o Kafka)
    parser_prod = subparsers.add_parser("produce-events", help="Produz eventos para Kafka")
    # Adiciona o argumento --quantidade para definir o número de eventos sintéticos a enviar
    parser_prod.add_argument("--quantidade", type=int, default=10, help="Número de eventos")
    # Vincula o subcomando à função que dispara a produção de eventos no Kafka
    parser_prod.set_defaults(func=_cmd_produce_events)

    # 21. Subcomando: consume-events (Consome e valida eventos do Kafka)
    parser_cons = subparsers.add_parser("consume-events", help="Consome eventos do Kafka")
    # Adiciona o argumento --max-mensagens para limitar a quantidade de eventos a serem consumidos
    parser_cons.add_argument("--max-mensagens", type=int, default=100, help="Máximo de mensagens")
    # Vincula o subcomando à função que executa o consumo e validação de mensagens
    parser_cons.set_defaults(func=_cmd_consume_events)

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


# Define o comando CLI para treinar/calcular o modelo de popularidade
def _cmd_train_popularity(args: argparse.Namespace) -> None:
    # Docstring descrevendo o comando de treino do modelo
    """Treina modelo de popularidade."""
    # Importação tardia da função calcular_popularidade para otimizar o tempo de inicialização da CLI
    from cinelake.recommender.popularity import calcular_popularidade

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa a função que calcula a popularidade dos filmes
    df = calcular_popularidade()
    # Exibe no log os 10 primeiros filmes com maior score de popularidade
    logger.info("Top 10 filmes populares:\n%s", df.head(10))


# Define o comando CLI para gerar recomendações populares e persistir no banco de dados
def _cmd_generate_popular(args: argparse.Namespace) -> None:
    # Docstring descrevendo o comando de geração e gravação das recomendações
    """Gera recomendações populares e grava na tabela."""
    # Importação tardia da função gerar_recomendacoes_populares
    from cinelake.recommender.popularity import gerar_recomendacoes_populares

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Invoca a função que gera e grava as recomendações no banco de dados passando a quantidade top_n
    gerar_recomendacoes_populares(top_n=args.top_n)
    # Registra no log a confirmação da geração das recomendações
    logger.info("Recomendações geradas")


# Define o comando CLI para treinar/calcular a similaridade de itens baseada em conteúdo
def _cmd_train_content_based(args: argparse.Namespace) -> None:
    # Docstring do comando de cálculo de similaridade content-based
    """Treina/calcula similaridade content-based."""
    # Importação tardia da função calcular_similaridade_itens
    from cinelake.recommender.content_based import calcular_similaridade_itens

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa o cálculo de similaridade de itens por conteúdo
    df = calcular_similaridade_itens()
    # Registra no log a quantidade de pares de similaridade calculados
    logger.info("Similaridade content-based calculada: %d pares", len(df))


# Define o comando CLI para gerar e salvar as recomendações baseadas em conteúdo
def _cmd_generate_content_based(args: argparse.Namespace) -> None:
    # Docstring do comando de geração de recomendações content-based
    """Gera recomendações content-based."""
    # Importação tardia da função gerar_recomendacoes_content_based
    from cinelake.recommender.content_based import gerar_recomendacoes_content_based

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa a geração de recomendações passando a quantidade top_n
    gerar_recomendacoes_content_based(top_n=args.top_n)
    # Registra no log a conclusão do processo
    logger.info("Recomendações content-based geradas")


# Define o comando CLI para treinar/calcula a similaridade colaborativa item-item
def _cmd_train_collaborative(args: argparse.Namespace) -> None:
    # Docstring do comando de cálculo de similaridade colaborativa
    """Treina/calcula similaridade colaborativa."""
    # Importação tardia da função calcular_similaridade_itens_colaborativa
    from cinelake.recommender.collaborative import (
        calcular_similaridade_itens_colaborativa,
    )

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa o cálculo da similaridade colaborativa
    df = calcular_similaridade_itens_colaborativa()
    # Registra no log a quantidade de pares de similaridade calculados
    logger.info("Similaridade colaborativa calculada: %d pares", len(df))


# Define o comando CLI para gerar e salvar as recomendações colaborativas item-item
def _cmd_generate_collaborative(args: argparse.Namespace) -> None:
    # Docstring do comando de geração de recomendações colaborativas
    """Gera recomendações colaborativas."""
    # Importação tardia da função gerar_recomendacoes_colaborativas
    from cinelake.recommender.collaborative import gerar_recomendacoes_colaborativas

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa a geração de recomendações colaborativas com o parâmetro top_n
    gerar_recomendacoes_colaborativas(top_n=args.top_n)
    # Registra no log a conclusão do processo
    logger.info("Recomendações colaborativas geradas")


# Define o comando CLI para gerar e salvar as recomendações híbridas
def _cmd_generate_hybrid(args: argparse.Namespace) -> None:
    # Docstring do comando de geração de recomendações híbridas
    """Gera recomendações híbridas."""
    # Importação tardia da função gerar_recomendacoes_hibridas
    from cinelake.recommender.hybrid import gerar_recomendacoes_hibridas

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa a geração de recomendações híbridas passando os pesos e top_n
    gerar_recomendacoes_hibridas(
        top_n=args.top_n, peso_content=args.peso_content, peso_collab=args.peso_collab
    )
    # Registra no log a conclusão do processo
    logger.info("Recomendações híbridas geradas")


# Define o comando CLI para executar a avaliação unificada de todos os modelos
def _cmd_evaluate_all_models(args: argparse.Namespace) -> None:
    # Docstring do comando de avaliação de modelos
    """Avalia todos os modelos."""
    # Importação tardia da função avaliar_todos_modelos
    from cinelake.recommender.evaluate import avaliar_todos_modelos

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Executa a avaliação de todos os modelos salvos para o limite top_k
    resultados = avaliar_todos_modelos(top_k=args.top_k)
    # Percorre e imprime os resultados obtidos para cada modelo
    for res in resultados:
        # Imprime o resultado individual do modelo
        print(res)
    # Registra no log a conclusão da avaliação de todos os modelos
    logger.info("Avaliação de todos os modelos concluída")


# Define o comando CLI para iniciar o servidor web da API principal usando Uvicorn
def _cmd_serve_main(args: argparse.Namespace) -> None:
    # Docstring do comando de inicialização da API principal
    """Inicia o servidor FastAPI principal."""
    # Importação tardia do Uvicorn para servir a aplicação ASGI
    import uvicorn
    # Importação tardia da aplicação FastAPI principal com suporte a cache Redis
    from cinelake.api.main import app

    # Obtém o logger configurado para este módulo
    logger = logging.getLogger(__name__)
    # Registra no log o endereço de host e porta em que a API principal está sendo iniciada
    logger.info("Iniciando API principal em %s:%s", args.host, args.port)
    # Executa o servidor Uvicorn escutando nos parâmetros informados via CLI
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


# Define a função de tratamento para o comando de produção de eventos de teste no Kafka
def _cmd_produce_events(args: argparse.Namespace) -> None:
    # Docstring da função de tratamento do produtor
    """Produz eventos de teste."""
    # Importação tardia da função de produção de eventos do módulo de streaming
    from cinelake.streaming.producer import produzir_eventos

    # Obtém a instância do logger para este módulo
    logger = logging.getLogger(__name__)
    # Executa a geração e envio dos eventos para o tópico do Kafka passando a quantidade fornecida
    produzir_eventos(quantidade=args.quantidade)
    # Registra no log a confirmação da execução do comando de envio de eventos
    logger.info("Eventos produzidos")


# Define a função de tratamento para o comando de consumo e validação de eventos do Kafka
def _cmd_consume_events(args: argparse.Namespace) -> None:
    # Docstring da função de tratamento do consumidor
    """Consome eventos do Kafka."""
    # Importação tardia da função de consumo de eventos do módulo de streaming
    from cinelake.streaming.consumer import consumir_eventos

    # Obtém a instância do logger para este módulo
    logger = logging.getLogger(__name__)
    # Executa o loop de consumo do Kafka com o limite máximo de mensagens informado
    consumir_eventos(max_mensagens=args.max_mensagens)
    # Registra no log o encerramento do processo de consumo
    logger.info("Consumo encerrado")


# Ponto de entrada padrão para execução via módulo (ex: python -m cinelake)
if __name__ == "__main__":
    main()


