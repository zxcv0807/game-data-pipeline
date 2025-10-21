# 완전 자동화된 파이프라인

## 1단계: Airflow에 Spark 연결 정보 등록하기
Airflow가 Spark master에게 "이 작업 좀 실행해줘"라고 요청할 수 있도록 Spark의 주소를 알려줘야 한다.

1. Airflow UI에 접속
2. Admin > Connections > New Connections
3. 아래와 같이 정보 입력한 뒤에 Save
- Connection Id: spark_default
- Connection Type: Spark
- Host: spark://spark-master
- Port: 7077

## 2단계: challenger_data_dag.py 파일 수정
아래의 코드로 수정
```python
from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
# SparkSubmitOperator를 새로 import 합니다.
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

with DAG(
    dag_id="collect_and_process_challenger_data", # DAG ID를 더 명확하게 변경
    schedule="@daily",
    start_date=pendulum.datetime(2025, 10, 10, tz="Asia/Seoul"),
    catchup=False,
    tags=["game-data", "ETL"],
) as dag:
    # 작업 1: 데이터 수집 (기존과 동일)
    collect_data_task = BashOperator(
        task_id="collect_raw_data", # Task ID를 더 명확하게 변경
        bash_command="python /opt/airflow/project/collect_data.py",
    )

    # 작업 2: Spark로 데이터 처리 (신규 추가)
    process_data_task = SparkSubmitOperator(
        task_id="process_data_with_spark",
        # 1단계에서 만든 Connection ID 사용
        conn_id="spark_default",
        # 실행할 파이썬 스크립트 지정
        application="/opt/spark/work-dir/process_data.py",
        # 터미널에서 사용했던 --packages 옵션
        packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
        # 터미널에서 사용했던 --conf 옵션
        conf={"spark.jars.ivy": "/opt/spark/work-dir/.ivy2"},
    )

    # 작업 순서 정의: 수집 작업이 끝나면(>>) 처리 작업을 실행
    collect_data_task >> process_data_task
```

## 3단계: Airflow UI 에서 dag 실행
먼저 collect_raw_data 작업이 실행되고, 성공하면 초록색으로 바뀐다.
그 직후, process_data_with_spark 작업이 자동으로 실행된된다.
두 작업이 모두 초록색으로 바뀌면, 데이터 수집부터 가공, 최종 저장까지의 모든 과정이 완벽하게 자동화된 것이다.


## 실제 집계된 정보 활용
Spark groupBy 및 agg 함수를 사용하여 랭크별 평균 승률, 평균 LP, 플레이어 수를 계산하는 로직 구현하였다.
sql과 pyspark는 문법이 살짝 다르다. 
예를 들면 sql에서는 as를 주로 사용했었는데, pyspark에서는 alias로 사용한다.

agg()함수는 groupBy()함수와 함께 쓰이는, 그룹별 집계 계산을 수행한다.
groupBy("rank")로 'rank' 컬럼의 값이 같은 그룹끼리 묶은 것을
agg() 함수를 이용해 각 그룹별로 괄호 안에 지정된 계산을 수행한다.

lit()함수는 상수 값을 컬럼으로 추가할 때 사용된다.