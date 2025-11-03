from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from check_data_quality import check_data_quality

with DAG(
    dag_id="collect_and_process_challenger_data",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 10, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["game-data", "ETL"],
) as dag:
    # 작업 1: 데이터 수집 
    collect_data_task = BashOperator(
        task_id="collect_raw_data",
        bash_command="python /opt/airflow/project/collect_data.py",
    )

    # 작업 2: 데이터 품질 검사
    check_data_quality_task = PythonOperator(
        task_id="check_data_quality",
        python_callable=check_data_quality,
    )

    # 작업 3: Spark로 데이터 처리 
    process_data_task = SparkSubmitOperator(
        task_id="process_data_with_spark",
        conn_id="spark_default",
        application="/opt/airflow/project/process_data.py",
        packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,org.postgresql:postgresql:42.6.0",
        conf={"spark.jars.ivy": "/home/airflow/.ivy2"},
    )

    # 작업 순서 정의
    collect_data_task >> check_data_quality_task >> process_data_task