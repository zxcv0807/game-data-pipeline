# Spark 시작하기

## Spark 실행 환경 추가하기 (Docker Compose)
로컬 컴퓨터에 Spark를 직접 설치하는 것은 과정이 복잡하기에, 기존의 docker-compose.yaml파일에 Spark 서비스를 추가하여 Docker환경에서 실행한다.

이 때, Spark UI도 8080포트를 사용하기에, 기존의 Airflow UI와 충돌하게 된다.
그래서 Airflow의 포트를 8081:8080으로 수정하여, 해결한다.

python3가 포함된 안정적인 버전인 아래의 버전을 사용한다.
```yaml
    image: apache/spark:v3.5.1
```

## 스크립트 실행 및 확인
1. Docker Compose 재실행
Spark 서비스가 추가되었으니, Docker Compose를 다시 시작해야 한다.
```bash
# 기존 서비스를 모두 내리고
docker-compose down
# 수정한 설정으로 모든 서비스를 다시 시작합니다 (Airflow + Spark)
docker-compose up -d
# spark-submit 명령어 실행
docker-compose exec spark-master /opt/spark/bin/spark-submit \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  --conf spark.jars.ivy=/opt/spark/work-dir/.ivy2 \
  /opt/spark/work-dir/process_data.py
```
