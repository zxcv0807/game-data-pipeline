# 1. 공식 Airflow 이미지를 기반으로 시작합니다.
FROM apache/airflow:3.1.0

# 2. 관리자(root) 권한으로 전환하여 패키지를 설치합니다.
USER root

# 3. Debian 12의 표준 버전인 Java 17을 설치합니다.
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean

# 4. 보안을 위해 다시 원래의 airflow 사용자로 전환합니다.
USER airflow

# Spark 버전을 3.5.7로 고정하기 위해 pyspark를 직접 설치합니다.
RUN pip install --user pyspark==3.5.7