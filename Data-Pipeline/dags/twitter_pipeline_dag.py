from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

import os
import sys

# Adding scripts folder to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from logging_config import get_logger

logger = get_logger("dag_pipeline.log", logger_name=__name__)

"""
data_pipeline_dag.py

An Airflow DAG that orchestrates:
1. data_acquisition (downloading files)
2. data_preprocessing (parsing & cleaning)
3. data_indexing_elasticsearch (indexing into Elasticsearch)
4. es_query (searching)

Usage:
    - Place this file in your Airflow DAGs folder.
    - Ensure you have Airflow installed and your scripts (data_acquisition.py, data_preprocessing.py, etc.)
      accessible to the Airflow environment (via PYTHONPATH or installed as a package).
    - Start Airflow (scheduler + webserver), then enable this DAG from the Airflow UI.
"""

DATA_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
DATA_VERSION_1_PATH = os.path.join(DATA_BASE_DIR, "version_1")
DATA_VERSION_2_PATH = os.path.join(DATA_BASE_DIR, "version_2")
DATA_VERSION_3_PATH = os.path.join(DATA_BASE_DIR, "version_3")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 0
}

with DAG(
        dag_id="twitter_pipeline_dag",
        default_args=default_args,
        schedule_interval=None,   # or "0 6 * * *" for a daily schedule, etc.
        catchup=False
) as dag:

    # Task 1: Data Acquisition
    def run_data_acquisition():
        from data_acquisition import download_selected_files
        from data_versions import get_data_version
        download_selected_files(get_data_version(1), DATA_BASE_DIR)
        logger.info("Data Acquisition Successful")
    t1 = PythonOperator(
        task_id="acquire_data",
        python_callable=run_data_acquisition
    )

    # Task 2: Data Preprocessing
    def run_data_preprocessing():
        from data_preprocessing import parse_folder

        data_dict = parse_folder(DATA_VERSION_1_PATH)
        logger.info("Length of the dictionary: %d", len(data_dict))
        logger.info("Data Preprocessing Successful")
    t2 = PythonOperator(
        task_id="preprocess_data",
        python_callable=run_data_preprocessing
    )

    # Task 3: Data Indexing into Elasticsearch
    def run_data_indexing():
        from data_indexing_elasticsearch import get_index_name, index_elasticsearch
        from data_preprocessing import parse_folder

        data_dict = parse_folder(DATA_VERSION_1_PATH)
        logger.info(f"Parsed {len(data_dict)} records")

        try:
            index_name = get_index_name(1)
            logger.info(f"Indexing data to {index_name}")
            index_elasticsearch(data_dict, index_name)
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            raise
    t3 = PythonOperator(
        task_id="index_data",
        python_callable=run_data_indexing
    )

    # Task 4: Query Elasticsearch
    def run_es_query():
        from es_query import search_custom
        from data_indexing_elasticsearch import get_index_name
        query = "russia war end"
        hits = search_custom(get_index_name(1), query, size=10)
        logger.info("Search results:")
        for hit in hits:
            tweet_id = hit.get("_id", "unknown")
            score = hit.get("_score", 0)
            text = hit.get("_source", {}).get("text", "")
            logger.info(f"Tweet ID: {tweet_id}, Score: {score}, Text: {text}")
            print(f"Tweet ID: {tweet_id}\nScore: {score}\nText: {text}\n{'-'*40}")
        logger.info("Data Querying Successful")
    t4 = PythonOperator(
        task_id="query_data",
        python_callable=run_es_query
    )

    # Set the task dependencies to run in sequence:
    t1 >> t2 >> t3 >> t4
