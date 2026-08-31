"""Avaliação do sistema RAG usando métricas de recuperação."""

import json  # Importa o módulo nativo para manipulação de arquivos no formato JSON.
import logging  # Importa o módulo nativo para geração de logs de execução e depuração.
from datetime import (  # Importa utilitários de data e hora com suporte a fusos horários (UTC).
    datetime,
    timezone,
)
from pathlib import (
    Path,  # Importa a classe Path para manipulação orientada a objetos de caminhos de arquivos.
)
from typing import Any  # Importa Any para anotações genéricas de tipos.

from sqlalchemy import (
    text,  # Importa a função text do SQLAlchemy para execução de queries SQL puras/parametrizadas.
)

from cinelake.db import (
    get_engine,  # Importa a função utilitária que obtém a conexão (engine) com o banco de dados SQLAlchemy.
)
from cinelake.rag.retriever import (
    buscar_documentos_similares,  # Importa a função de busca por similaridade de vetor/documento no RAG.
)

logger = logging.getLogger(__name__)  # Inicializa o logger específico para este módulo usando o nome do arquivo/módulo atual.


def carregar_dataset(caminho: Path) -> list[dict[str, Any]]:  # Define a função para carregar a lista de perguntas e gabarito do arquivo JSON.
    """Carrega o dataset de avaliação."""  # Docstring descrevendo o propósito da função carregar_dataset.
    with caminho.open("r", encoding="utf-8") as f:  # Abre o arquivo especificado em caminho no modo de leitura com codificação UTF-8.
        dados = json.load(f)  # Converte o conteúdo textual do arquivo JSON em um dicionário Python.
    return list(dados["perguntas"])  # Retorna apenas a lista associada à chave "perguntas" contida no dicionário carregado.


def calcular_recall_k(relevantes: list[str], recuperados: list[str], k: int) -> float:  # Define a função que calcula a métrica Recall@k.
    """Calcula recall@k."""  # Docstring descrevendo o propósito da função calcular_recall_k.
    if not relevantes:  # Verifica se a lista de documentos relevantes está vazia.
        return 0.0  # Retorna 0.0 caso não existam documentos relevantes para evitar divisão por zero.
    recuperados_top_k = recuperados[:k]  # Trunca a lista de documentos recuperados para considerar apenas os primeiros k elementos.
    acertos = len(set(relevantes) & set(recuperados_top_k))  # Calcula a interseção entre os conjuntos de relevantes e recuperados no top-k.
    return acertos / len(relevantes)  # Retorna a proporção de documentos relevantes encontrados no top-k em relação ao total de relevantes.


def calcular_mrr(relevantes: list[str], recuperados: list[str]) -> float:  # Define a função para calcular o Mean Reciprocal Rank (MRR).
    """Calcula MRR (Mean Reciprocal Rank) para uma consulta."""  # Docstring descrevendo o propósito da função calcular_mrr.
    for i, doc in enumerate(recuperados, start=1):  # Percorre a lista de documentos recuperados acompanhada do índice 1-based (posição).
        if doc in relevantes:  # Verifica se o documento recuperado na posição i pertence ao conjunto de documentos relevantes.
            return 1.0 / i  # Retorna o inverso da primeira posição (1/rank) onde o documento relevante apareceu.
    return 0.0  # Retorna 0.0 caso nenhum dos documentos recuperados esteja na lista de relevantes.


def calcular_hit_rate_k(relevantes: list[str], recuperados: list[str], k: int) -> bool:  # Define a função que calcula a taxa de sucesso (Hit Rate@k).
    """Retorna True se pelo menos um relevante está nos top-k."""  # Docstring descrevendo o propósito da função calcular_hit_rate_k.
    return bool(set(relevantes) & set(recuperados[:k]))  # Retorna True se houver interseção entre os relevantes e os top-k recuperados, senão False.


def avaliar_rag(dataset_path: Path, k: int = 5) -> dict[str, Any]:  # Define a função principal de avaliação do pipeline RAG.
    """
    Executa avaliação do RAG.

    Args:
        dataset_path: Caminho para o JSON de perguntas.
        k: Número de documentos top-k a considerar.

    Returns:
        Resumo com métricas.
    """  # Docstring detalhada da função avaliar_rag descrevendo parâmetros e retorno.
    logger.info("Iniciando avaliação RAG")  # Registra no log que o processo de avaliação do RAG foi iniciado.

    perguntas = carregar_dataset(dataset_path)  # Carrega as perguntas e gabarito chamando a função carregar_dataset.

    metricas: dict[str, list[float]] = {  # Inicializa o dicionário de métricas agregadas com listas vazias para cada indicador.
        "recall": [],  # Lista para armazenar as pontuações de recall de cada pergunta.
        "mrr": [],  # Lista para armazenar os valores de MRR de cada pergunta.
        "hit_rate": [],  # Lista para armazenar as pontuações de hit rate (1.0 ou 0.0) de cada pergunta.
    }  # Fecha a declaração da estrutura de dados metricas.

    resultados = []  # Inicializa uma lista vazia para armazenar o detalhamento do resultado individual de cada pergunta.

    for pergunta in perguntas:  # Itera sobre cada item (dicionário de pergunta) do dataset de perguntas.
        texto = pergunta["texto"]  # Extrai a string com o texto da pergunta a ser enviada ao retriever.
        relevantes = pergunta["documentos_relevantes"]  # Extrai a lista de documentos relevantes esperados para essa pergunta.
        docs_recuperados = buscar_documentos_similares(texto, top_k=k)  # Executa a busca vetorial por documentos similares no RAG.
        titulos_recuperados = [doc["titulo"] for doc in docs_recuperados]  # Extrai apenas os títulos da lista de documentos retornados pela busca.

        recall = calcular_recall_k(relevantes, titulos_recuperados, k)  # Calcula a métrica Recall@k para a pergunta atual.
        mrr = calcular_mrr(relevantes, titulos_recuperados)  # Calcula o valor de MRR para a pergunta atual.
        hit = calcular_hit_rate_k(relevantes, titulos_recuperados, k)  # Verifica se ocorreu Hit@k para a pergunta atual.

        metricas["recall"].append(recall)  # Adiciona o recall calculado na lista acumuladora de recall.
        metricas["mrr"].append(mrr)  # Adiciona o MRR calculado na lista acumuladora de MRR.
        metricas["hit_rate"].append(1.0 if hit else 0.0)  # Adiciona 1.0 (para True) ou 0.0 (para False) na lista acumuladora de hit rate.

        resultados.append(  # Adiciona o dicionário detalhado com o resultado da pergunta atual na lista resultados.
            {  # Abre a estrutura do dicionário de resultados da pergunta.
                "pergunta_id": pergunta["id"],  # Armazena o identificador único da pergunta.
                "texto": texto,  # Armazena o texto da pergunta avaliada.
                "relevantes": relevantes,  # Armazena a lista de documentos esperados como relevantes.
                "recuperados": titulos_recuperados,  # Armazena a lista de títulos que o RAG efetivamente recuperou.
                "recall": recall,  # Armazena a pontuação de recall calculada para a pergunta.
                "mrr": mrr,  # Armazena a pontuação de MRR calculada para a pergunta.
                "hit": hit,  # Armazena o resultado booleano de Hit Rate.
            }  # Fecha a estrutura do dicionário individual.
        )  # Fecha a chamada do método append na lista resultados.
        logger.info(  # Emite uma mensagem informativa no log contendo os resultados individuais da pergunta.
            "Pergunta %s: recall=%.2f mrr=%.2f hit=%s",  # String de formatação do log exibindo id, recall, mrr e hit rate.
            pergunta["id"], recall, mrr, hit,  # Parâmetros passados para substituir os especificadores de formato no log.
        )  # Fecha a função logger.info.

    # Calcula médias  # Comentário de seção indicando o início do cálculo estatístico final das métricas.
    resumo = {  # Declara o dicionário que conterá a média geral de todas as perguntas avaliadas.
        "total_perguntas": len(perguntas),  # Conta e armazena o número total de perguntas avaliadas.
        "recall_medio": sum(metricas["recall"]) / len(metricas["recall"]) if metricas["recall"] else 0.0,  # Calcula a média do recall se houver perguntas, senão 0.0.
        "mrr_medio": sum(metricas["mrr"]) / len(metricas["mrr"]) if metricas["mrr"] else 0.0,  # Calcula a média do MRR se houver perguntas, senão 0.0.
        "hit_rate_medio": sum(metricas["hit_rate"]) / len(metricas["hit_rate"]) if metricas["hit_rate"] else 0.0,  # Calcula a taxa média de acerto (hit rate) geral.
    }  # Fecha a declaração do dicionário resumo.

    # Registra em ingestion_batch  # Comentário indicando a chamada da função para auditoria/registro no banco de dados.
    _registrar_avaliacao(resumo, len(perguntas))  # Invoca a função privada para salvar a execução na tabela ingestion_batch.

    # Salva resultado detalhado  # Comentário de seção indicando o salvamento do relatório em formato JSON em disco.
    saida = Path("data/rag/evaluation/results.json")  # Define o caminho do arquivo onde o relatório final será gravado.
    saida.parent.mkdir(parents=True, exist_ok=True)  # Garante que os diretórios pai (data/rag/evaluation) existam antes de criar o arquivo.
    with saida.open("w", encoding="utf-8") as f:  # Abre o arquivo de saída no modo de escrita ('w') com suporte a caracteres UTF-8.
        json.dump({"resumo": resumo, "resultados": resultados}, f, ensure_ascii=False, indent=2)  # Escreve o JSON formatado no arquivo com indentação.

    logger.info("Avaliação concluída: %s", resumo)  # Registra no log que a avaliação foi finalizada, exibindo o resumo numérico.
    return resumo  # Retorna o dicionário resumo com as médias globais calculadas.


def _registrar_avaliacao(resumo: dict[str, Any], total_perguntas: int) -> None:  # Define a função auxiliar privada para registrar métricas no banco de dados.
    """Registra execução em ingestion_batch."""  # Docstring descrevendo a responsabilidade da função _registrar_avaliacao.
    engine = get_engine()  # Instancia/obtém o objeto engine do banco de dados chamando get_engine().
    with engine.begin() as conn:  # Abre uma transação no banco de dados que faz commit automático ao finalizar sem erros.
        agora = datetime.now(timezone.utc)  # Obtém o timestamp atual com fuso horário UTC zerado/alinhado.
        conn.execute(  # Executa o comando de inserção de dados via query SQL.
            text("""
                INSERT INTO ingestion_batch (source, status, started_at, finished_at, rows_processed, rows_inserted, error_message)
                VALUES ('rag_evaluation', 'success', :agora, :agora, :total, :total, NULL)
            """),  # Query SQL utilizando placeholders parametrizados para prevenir SQL Injection.
            {"agora": agora, "total": total_perguntas},  # Dicionário de parâmetros mapeando as variáveis da query SQL (:agora e :total).
        )  # Fecha a chamada conn.execute.
