import csv
from pathlib import Path
from datetime import datetime, timedelta

data_dir = Path("I:/Meus_Projetos/Github/CineLake-AI/powerbi/dados")
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Pipeline Executions & Observability (Histórico de Execuções)
with open(data_dir / "pipeline_observability.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Pipeline_Name", "Layer", "Engine", "Status", "Duration_Sec", 
        "Duration_Formatted", "Rows_Read", "Rows_Written", "Data_Quality_Tests", 
        "Tests_Passed", "Freshness_Hours", "Execution_Date", "Error_Message"
    ])
    
    # 7 dias de execuções realistas
    base_date = datetime.now()
    pipelines = [
        ("dag_ingestion_movies_tmdb", "Bronze", "Airflow + Python", 45, "00:00:45", 9742, 9742, 8, 8, 1.2, ""),
        ("dag_ingestion_ratings_stream", "Bronze", "Airflow + Kafka", 120, "00:02:00", 100836, 100836, 12, 12, 0.8, ""),
        ("dag_ingestion_tags_raw", "Bronze", "Airflow + Python", 30, "00:00:30", 3683, 3683, 6, 6, 1.5, ""),
        ("dbt_stg_movies_cleansing", "Silver", "dbt Core + Postgres", 85, "00:01:25", 9742, 9742, 15, 15, 2.0, ""),
        ("dbt_stg_ratings_dedup", "Silver", "dbt Core + Postgres", 195, "00:03:15", 100836, 100836, 20, 20, 2.1, ""),
        ("dbt_dim_movie_enrichment", "Gold", "dbt Core", 60, "00:01:00", 9742, 9742, 10, 10, 2.4, ""),
        ("dbt_fact_ratings_mart", "Gold", "dbt Core", 140, "00:02:20", 100836, 100836, 18, 18, 2.4, ""),
        ("spark_recommendation_hybrid", "Gold / ML", "PySpark", 310, "00:05:10", 610, 610, 14, 14, 3.0, "")
    ]
    
    for days_ago in range(7, -1, -1):
        curr_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        for p in pipelines:
            status = "Success"
            err = ""
            # Simula uma única falha tratada há 4 dias para dar realismo de DataOps (99.2% SLA)
            if days_ago == 4 and "ratings_stream" in p[0]:
                status = "Failed"
                err = "Kafka connection timeout: retrying with backoff"
            
            writer.writerow([
                p[0], p[1], p[2], status, p[3], p[4], p[5], p[6], p[7], 
                p[8] if status == "Success" else p[8] - 1, 
                p[9] + (days_ago * 0.2), curr_date, err
            ])

# 2. Executive DataOps KPIs
with open(data_dir / "dataops_kpis.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Indicador", "Valor", "Meta", "Status_SLA", "Descricao"])
    writer.writerow(["SLA Global de Pipelines", "99.4%", ">= 99.0%", "Conforme", "Disponibilidade dos pipelines nos últimos 30 dias"])
    writer.writerow(["Freshness Médio dos Dados", "2.1 horas", "<= 24.0 horas", "Conforme", "Tempo médio desde a última ingestão"])
    writer.writerow(["Data Quality Pass Rate", "100.0%", "100.0%", "Conforme", "Testes de integridade (dbt + Great Expectations)"])
    writer.writerow(["Pipelines Monitorados", "8 DAGs", "8 DAGs", "Conforme", "Pipelines ativos nas camadas Bronze, Silver e Gold"])
    writer.writerow(["Volumetria Total Processada", "1.85M linhas", "1.50M linhas", "Conforme", "Total de registros processados na semana"])
    writer.writerow(["MTTR (Tempo Médio de Recuperação)", "14 min", "< 30 min", "Conforme", "Tempo médio para recuperação automática de jobs"])

print("CSVs de Engenharia gerados com sucesso em:", data_dir)
