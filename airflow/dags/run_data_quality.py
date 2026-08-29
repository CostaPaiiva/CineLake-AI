# ==============================================================================
# run_data_quality.py - DAG do Apache Airflow para Validação de Qualidade
# ==============================================================================
"""DAG para executar validação de qualidade de dados com Great Expectations."""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Adiciona o diretório raiz do projeto ao PYTHONPATH para importar o pacote cinelake
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from cinelake.data_quality.validate import validar_ratings

# Argumentos padrão aplicados a todas as tasks da DAG
default_args = {
    'owner': 'cinelake',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definição e configuração da DAG
with DAG(
    dag_id='run_data_quality',
    default_args=default_args,
    description='Validação de qualidade dos dados com Great Expectations',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['quality', 'ge'],
) as dag:

    def _validar_qualidade(ti=None):
        """
        Função executada pelo PythonOperator para chamar a validação de ratings.
        Interrompe a DAG se a validação indicar falha de qualidade.
        """
        resultado = validar_ratings()
        if not resultado['success']:
            raise ValueError("Validação de qualidade falhou")
        return resultado

    # Task principal de validação de dados via Great Expectations
    validar_qualidade_task = PythonOperator(
        task_id='validar_ratings',
        python_callable=_validar_qualidade,
    )