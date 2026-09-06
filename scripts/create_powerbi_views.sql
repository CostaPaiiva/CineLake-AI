-- =====================================================================
-- Views analíticas para Power BI
-- Script SQL para criação das views de mart analítico para dashboards Power BI
-- =====================================================================

-- ---------------------------------------------------------------------
-- View 1: Executive Overview (Visão Executiva do Sistema)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_powerbi_executive_overview AS -- Cria ou substitui a view de visão geral executiva
SELECT -- Inicia a seleção dos indicadores executivos principais
    (SELECT COUNT(DISTINCT user_id) FROM ratings) AS total_usuarios, -- Contagem total de usuários únicos que realizaram avaliações na tabela ratings
    (SELECT COUNT(*) FROM movies) AS total_filmes, -- Contagem total de filmes cadastrados na tabela movies
    (SELECT COUNT(*) FROM ratings) AS total_ratings, -- Contagem total de avaliações registradas na tabela ratings
    (SELECT COUNT(*) FROM event_log) AS total_interacoes, -- Contagem total de eventos/interações registrados na tabela event_log
    (SELECT COUNT(*) FROM recommendations WHERE model_name = 'hybrid') AS total_recomendacoes_geradas, -- Total de recomendações geradas especificamente pelo modelo híbrido
    (SELECT COUNT(*) FROM event_log WHERE event_type = 'recommendation_click') AS total_cliques_recomendacao, -- Total de cliques em recomendações registrados no log de eventos
    CASE WHEN (SELECT COUNT(*) FROM event_log WHERE event_type = 'recommendation_view') > 0 -- Verifica se houve ao menos uma visualização de recomendação para evitar divisão por zero
         THEN (SELECT COUNT(*) FROM event_log WHERE event_type = 'recommendation_click')::float / -- Calcula a taxa de clique dividindo o total de cliques
              (SELECT COUNT(*) FROM event_log WHERE event_type = 'recommendation_view')::float -- pelo total de visualizações de recomendação (convertidos para float)
         ELSE 0 -- Retorna 0 caso não existam visualizações de recomendação registradas
    END AS ctr_recomendacao, -- Define o alias da métrica de Taxa de Clique (Click-Through Rate - CTR)
    (SELECT MAX(ingestion_timestamp) FROM event_log) AS ultima_interacao, -- Obtém o registro de data/hora da interação mais recente no event_log
    (SELECT COUNT(DISTINCT user_id) FROM event_log WHERE ingestion_timestamp > NOW() - INTERVAL '7 days') AS usuarios_ativos_7d; -- Conta usuários únicos com interação nos últimos 7 dias

-- ---------------------------------------------------------------------
-- Tabela Pré-requisito: model_metrics (garante a existência da tabela)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_metrics ( -- Cria a tabela de métricas caso ela ainda não exista
    model_name VARCHAR(100) PRIMARY KEY, -- Nome do modelo de recomendação como chave primária
    precision_medio FLOAT, -- Valor da precisão média obtida para o modelo
    recall_medio FLOAT, -- Valor do recall médio obtido para o modelo
    hit_rate FLOAT -- Valor do Hit Rate obtido para o modelo
); -- Conclui a criação preventiva da tabela model_metrics

-- ---------------------------------------------------------------------
-- View 2: Recommendation Analytics (Métricas e Performance dos Modelos)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_powerbi_recommendation_analytics AS -- Cria ou substitui a view de análise de desempenho das recomendações
SELECT -- Inicia a seleção das métricas dos modelos de recomendação
    model_name, -- Nome identificador do modelo de recomendação
    precision_medio, -- Média da precisão obtida para o modelo
    recall_medio, -- Média do recall obtido para o modelo
    hit_rate -- Taxa de acerto (Hit Rate) alcançada pelo modelo
FROM model_metrics; -- Tabela fonte contendo as métricas de avaliação salvas dos modelos

-- ---------------------------------------------------------------------
-- View 3: Data Engineering Monitoring (Monitoramento dos Pipelines)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW mart_powerbi_data_engineering_monitoring AS -- Cria ou substitui a view de monitoramento de engenharia de dados
SELECT -- Inicia a seleção dos indicadores de execução das cargas de dados
    source, -- Origem da carga ou nome da fonte de dados de ingestão
    status, -- Status da execução do pipeline (ex: success, failed, in_progress)
    MAX(finished_at) AS ultima_execucao, -- Obtém a data/hora do término da execução mais recente
    MAX(rows_processed) AS rows_processed, -- Obtém o maior volume de linhas processadas registradas
    MAX(rows_inserted) AS rows_inserted, -- Obtém o maior volume de linhas inseridas registradas
    MAX(rows_updated) AS rows_updated, -- Obtém o maior volume de linhas atualizadas registradas
    MAX(finished_at) - MIN(started_at) AS duracao, -- Calcula a diferença de tempo/duração entre o início mais antigo e fim mais recente
    CASE WHEN status = 'failed' THEN 1 ELSE 0 END AS pipeline_failed, -- Flag numérico de falha: 1 se status for 'failed', 0 caso contrário
    EXTRACT(EPOCH FROM (NOW() - MAX(finished_at)))/3600.0 AS freshness_horas -- Calcula o tempo em horas decorrido desde a última execução bem-sucedida/concluída
FROM ingestion_batch -- Tabela fonte contendo os registros de execução das cargas em lote
GROUP BY source, status; -- Agrupa as métricas de monitoramento por fonte de dados e status de execução
