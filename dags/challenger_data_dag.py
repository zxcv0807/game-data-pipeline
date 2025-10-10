from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="collect_challenger_data_daily", # Airflow UI에 표시될 DAG의 고유 ID
    schedule="@daily", # 실행 주기 (매일 자정)
    start_date=pendulum.datetime(2025, 10, 10, tz="Asia/Seoul"), # 이 DAG가 언제부터 유효한지
    catchup=False, # 시작일로부터 놓친 작업을 한 번에 실행할지 여부 (False 권장)
    tags=["game-data", "collection"], # 검색하기 쉽도록 태그 추가
) as dag:
    # 작업(Task) 정의: Bash 명령어를 실행하는 오퍼레이터를 사용
    collect_data_task = BashOperator(
        task_id="run_collection_script", # DAG 내에서 이 작업의 고유 ID
        # Docker 컨테이너 내에서 스크립트를 실행할 경로를 지정해야 합니다.
        # 보통 docker-compose.yaml 설정 시 프로젝트 폴더를 마운트합니다.
        bash_command="python /opt/airflow/project/collect_data.py", 
    )