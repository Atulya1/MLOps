from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

# from logging_config import get_logger
# logger = get_logger(__name__)

default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 0
}

def task_one():
    print("Hello from Task One!")
    return "Task One Complete"

def task_two():
    print("Hello from Task Two!")
    return "Task Two Complete"

with DAG(
        dag_id="dag_test",
        default_args=default_args,
        schedule=None,
        catchup=False
) as dag:

    t1 = PythonOperator(
        task_id="test_task_one",
        python_callable=task_one
    )

    t2 = PythonOperator(
        task_id="test_task_two",
        python_callable=task_two
    )

    t1 >> t2
