from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

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

    # 작업 2: Spark로 데이터 처리 
    process_data_task = SparkSubmitOperator(
        task_id="process_data_with_spark",
        # 1단계에서 만든 Connection ID 사용
        conn_id="spark_default",
        # 실행할 파이썬 스크립트 지정
        application="/opt/airflow/project/process_data.py",
        # 터미널에서 사용했던 --packages 옵션
        packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
        # 터미널에서 사용했던 --conf 옵션
        conf={"spark.jars.ivy": "/home/airflow/.ivy2"},
    )

    # 작업 순서 정의
    collect_data_task >> process_data_task