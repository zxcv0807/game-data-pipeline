# 완전 자동화된 파이프라인 에러 해결

## Airflow UI에서 Connections에서 Connection Type에 Spark가 보이지 않는다.

1. Airflow의 기본 Docker 이미지에는 Apache Spark와 통신하는데 필요한 Provider가 기본으로 설치되어 있지 않다.

=> docker-compose.yaml 파일 수정
_PIP_ADDITIONAL_REQUIREMENTS 항목이 비어져 있는데, 이를 Airflow 컨테이너가 시작될 때마다 자동으로 Spark Provider를 설치하게 설정하는 것이다.
```YAML
x-airflow-common:
  &airflow-common
  # ... (생략) ...
  environment:
    &airflow-common-env
    # ... (여러 환경 변수들) ...
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-apache-airflow-providers-apache-spark}
```

2. _PIP_ADDITIONAL_REQUIREMENTS에 apache-airflow-providers-apache-spark를 추가하면 unhealthy 문제가 발생한다.
Airflow 컨테이너는 시작될 때마다 인터넷에서 해당 패키지를 다운로드하고 설치하는 과정을 거치는데, 
이 과정이 생각보다 시간이 오래 걸린다.
기존의 healthcheck 에서 start_period가 60s로 설정되어 있어, Docker가 정해진 시간에 응답이 없어서 unhealthy라고 판단하고 에러를 발생시킨다.

=> start_period를 늘려준다.
```YAML
airflow-apiserver:
  # ... (생략) ...
  healthcheck:
    # ... (생략) ...
    start_period: 1200s # 60s 에서 1200s 로 넉넉하게.
```


## JAVA 미설치
Airflow 컨테이너가 Spark 작업을 실행하려고 하는데, Spark를 실행하는데 필수적인 JAVA가 설치되어 있지 않다.

=> Dockerfile 생성하기, docker-compose.yaml 수정정
```Dockerfile
# 1. 공식 Airflow 이미지를 기반으로 시작합니다.
FROM apache/airflow:3.1.0
# 2. 관리자(root) 권한으로 전환하여 패키지를 설치합니다.
USER root
# 3. Debian 12의 표준 버전인 Java 17을 설치합니다.
# airflow 3.1.0은 Debian 12를 기반으로 만들어 졌다. Debian 12의 기본 패키지 저장소(apt)에는 보안과 안정성을 위해 OpenJDK 17이 기본 Java 버전으로 등록되어 있다.
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean
# 4. 보안을 위해 다시 원래의 airflow 사용자로 전환합니다.
USER airflow
```

```YAML
x-airflow-common:
  &airflow-common
  # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.1.0} # 이 줄을 주석 처리하고
  build: . # 이 줄의 주석을 해제하거나 추가합니다.
  # ...
```

## 파일 경로 에러
DAG 파일에서 conf={"spark.jars.ivy": "/opt/spark/work-dir/.ivy2"} 라고 설정한 것은,
Airflow worker에게 Spark master 컨테이너를 사용하라는 의미이다. 하지만 Airflow worker는 spark master 컨테이너의 폴더에 접근할 권한이 없다.
결과적으로 Airflow Worker는 존재하지도 않고 권한도 없는 경로에 파일을 쓰려고 시도하다가 FileNotFoundException 에러를 발생시킨 것이다.

=> 경로를 수정. airflow의 홈 디렉토리에 Ivy 캐시를 성공적으로 생성하고 라이브러리를 다운로드한 뒤, Spark Master에게 작업을 올바르게 요청할 것이다.
```python 
process_data_task = SparkSubmitOperator(
    # ... (생략) ...
    # 잘못된 경로: spark-master 컨테이너의 경로
    # conf={"spark.jars.ivy": "/opt/spark/work-dir/.ivy2"},

    # 올바른 경로: Airflow Worker 컨테이너가 쓸 수 있는 경로
    conf={"spark.jars.ivy": "/home/airflow/.ivy2"},
)
```


## 컨테이너 간의 통신 에러

Airflow Worker 컨테이너가 spark-submit 명령어를 통해 'spark://spark-master:7077' 주소로 Spark Master 컨테이너에게 작업을 요청했지만,
알 수 없는 이유로 두 컨테이너간의 통신이 실패했다.

=> 컨테이너 간의 통신망을 명시적으로 설정한다.
docker-compose.yaml 파일에서 아래와 같이 수정한다.
```YAML
# ... (volumes: postgres-db-volume: 다음 줄에)
networks:
  data-pipeline-net:
```
x-airflow-common 섹션과 postgres, redis, spark-master, spark-worker에 networks: 설정을 추가한다.
```YAML
x-airflow-common:
  &airflow-common
  # ... (image, environment 등)
  networks: # << 이 부분을 추가
    - data-pipeline-net
  user: "${AIRFLOW_UID:-50000}:0"
  # ... (depends_on)

postgres:
  # ... volumes
  networks:
    - data-pipeline-net
  # healthcheck ... 
redis:
  # ... expose
  networks:
    - data-pipeline-net
  # healthcheck ...

spark-master:
  # ... (image, environment 등)
  networks: # << 이 부분을 추가
    - data-pipeline-net
  # ...
spark-worker-1:
  # ... volumes
  networks:
    - data-pipeline-net
  # depends ...
```
이는 Airflow 관련 모든 서비스와 Spark master, worker 서비스는 data-pipeline-net 이라는 통신망을 사용하라고 명시하는 것이다.


## Airflow와 Spark의 경로 문제

- Airflow Worker 컨테이너: SparkSubmitOperator를 실행하는 주체이다.
- Spark Master 컨테이너: 실제 데이터를 처리를 담당한다.

SparkSubmitOperator는 기본적으로 'client' 모드로 작동한다. Spark 작업을 실행하는 메인 프로그램(process_data.py)이 Spark master에서 실행되는 것이 아니라,
Airflow Worker에서 직접 실행된다는 의미이다.
DAG 파일(challenger_data_dag.py)에 아래와 같이 적었기 때문이다.
application="/opt/spark/work-dir/process_data.py"
Airflow는 존재하지도 않는 경로의 파일을 실행하려다가 에러가 발생한 것이다.

=> 올바른 파일 경로 가르쳐 주기
```python
process_data_task = SparkSubmitOperator(
    task_id="process_data_with_spark",
    conn_id="spark_default",
    # 잘못된 경로: Spark Master 컨테이너 내부의 경로
    # application="/opt/spark/work-dir/process_data.py",

    # 올바른 경로: Airflow Worker 컨테이너 내부의 경로
    application="/opt/airflow/project/process_data.py",
    packages="org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    conf={"spark.jars.ivy": "/home/airflow/.ivy2"},
)
```


## AWS 자격 증명 문제제
process_data.py 파일에는 os.getenv()를 통해 AWS 자격 증명을 하고 있는데, 이는 spark-master에게만 AWS 키를 주고, 정작 airflow-worker에게는 AWS 키를 주지 않았다.
SparkSubmitOperator는 'client' 모드로 동작하기에 process_data.py는 Airflow worker 컨테이너 안에서 실행된다. 하지만 Airflow-worker 컨테이너는 AWS 자격 증명 환경 변수가 설정되어 있지 않다.

=> Airflow 관련 모든 서비스가 AWS 자격 증명을 알 수 있도록, docker-compose.yaml 파일에 AWS 키를 추가해준다.
```YAML
x-airflow-common:
  &airflow-common
  # ...
  environment:
    &airflow-common-env
    # -- 아래 두 줄을 추가해주세요 --
    AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    # ... (다른 Airflow 환경 변수들)
```


### Airflow 실패
Airflow UI 에서 실패 로그가 아래와 같은데, 'spark-submit'이 실패했는데 실패한 원인을 알 수 없었다.
AirflowException: Cannot execute: spark-submit ... Error code is: 1. 

=> 터미널에서 명령어로 직접 실행하여 에러 로그를 확인했다.
```bash
# airflow-worker 컨테이너로 들어간다.
docker-compose exec airflow-worker bash
```

```bash
# airflow 에서 실패했던 명령어를 직접 실행한다.
spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/home/airflow/.ivy2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  --name arrow-spark \
  --deploy-mode client \
  /opt/airflow/project/process_data.py
```

실행하게 되면 아래의 자바 에러가 발생한다.

Caused by: java.io.InvalidClassException: ... local class incompatible: stream classdesc serialVersionUID = ..., local class serialVersionUID = 

이는 같은 클래스를 사용하는데, 서로 다른 버전이기 때문에 문제가 발생하는 것이다.
Spark Provider를 설치할 때, 최신 버전인 spark 4.0.1 라이브러리를 설치했던 것을 알 수 있다.
우리는 docker-compose.yaml에서 apache/spark:3.5.7-python3 로 Spark 3.5.7 버전을 사용하고 있다.
버전이 일치하지 않아 발생한 문제이다.

=> Dockerfile 수정
```Dockerfile
# ... (생략) ...
USER root
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean
USER airflow
# -- 입주민(airflow)이 자신의 개인 공간에 직접 설치 --
RUN pip install --user pyspark==3.5.7
```


## Spark-worker 
에러메시지가 아래와 같다.
WARN TaskSchedulerImpl: Initial job has not accepted any resources; check your cluster UI to ensure that workers are registered and have sufficient resources
이는 Airflow Worker가 Spark 작업을 지시했는데, Spark master가 실제 일을 할 직원을 찾는 데, 일할 직원이 없다는 의미이다.

=> docker-compose.yaml 파일에 spark-worker를 추가하여 실제로 일할 직원을 만들어 준다.
```YAML
# ... (spark-master 서비스) ...
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master

  # -- 아래 spark-worker-1 서비스를 새로 추가해주세요! --
  spark-worker-1:
    image: apache/spark:3.5.7-python3
    user: root
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077 # 감독관의 주소를 알려줍니다.
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./:/opt/spark/work-dir
    networks:
      - data-pipeline-net
    depends_on: # 감독관이 준비될 때까지 기다립니다.
      - spark-master

volumes:
  postgres-db-volume:
# ... (이하 동일) ...
```

이렇게 되면 Spark-worker가 예전에 겪었던 에러와 비슷하게, 로그를 남기지도 않을 정도로 바로 종료되어 버려서, docker-compose ps 명령어에도 보이지 않고,
docker-compose logs spark-worker-1 을 해도 아무것도 보이지 않는다.

=> Worker만 실행하기
```bash
# spark-worker가 실행할 때 필요한 것만 백그라운드로 실행
docker-compose up -d postgres redis spark-master
# spark-worker 실행
docker-compose run spark-worker-1
```
실행하면 아래의 로그가 보인다.
[+] Creating 1/1

 ✔ Container de-project-spark-master-1  Running

이는 spark-worker-1이 시작하자마자 spark-master에 연결하려 했지만, master가 준비되지 않아, 연결에 실패하고, 즉시 종료되어 버렸다.
이를 레이스 컨디션(경쟁 상태)라고 한다.

worker가 master가 healthy가 될 때까지 기다리게 한다.

```yaml
spark-master:
  # ... (image, user, environment 등)
  volumes:
    - ./:/opt/spark/work-dir
  # -- healthcheck 블록을 새로 추가해주세요! --
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080"]
    interval: 10s
    timeout: 10s
    retries: 5
    start_period: 10s
  networks:
    - data-pipeline-net
  ports:
    # ...
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
```

```YAML
spark-worker-1:
  # ... (image, user, environment 등)
  volumes:
    - ./:/opt/spark/work-dir
  networks:
    - data-pipeline-net
  # -- depends_on 부분을 아래와 같이 수정해주세요! --
  depends_on:
    spark-master:
      condition: service_healthy
```

이렇게 해도 spark-worker는
spark-worker-1-1 exited with code 0
로그를 보이면서 바로 종료된다.

이는 spark-worker-1 서비스에 실행할 명령어가 명시되지 않았기 때문이다.
SPARK_MODE=worker 만으로는 컨테이너가 우리가 원하는 상시 대기 상태로 계속 실행되는 것을 보장하지 못한다.

=> spark-master를 해결했던 같은 방식으로, spark-worker-1에게도 실행할 정확한 명령어를 지정해준다.
```YAML
spark-worker-1:
  # ... 생략
  depends_on:
    spark-master:
      condition: service_healthy
  # -- 아래 command 블록을 새로 추가해주세요! --
  command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
```
추가한 command 블럭은 Master에 찾아가서 일이 끝날 떄까지 계속 대기하라고 지시하는 것이다.