# Airflow 시작

## 1단계: Airflow 공식 docker-compose.yaml 파일 다운로드
https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
위의 사이트에서 Airflow팀이 미리 만들어 둔 docker-compose.yaml을 다운로드하여 현재의 폴더로 가져온다.

## 2단계: 필수 폴더 생성 및 Airflow 초기화
1. 초기 설정
위에서 다운받은 docker-compose.yaml파일은 dags, logs, plugins 라는 폴더가 있다고 가정하고 만들어졌다.
그렇기에 해당 폴더들을 만들어 준다.

2. 환경 변수 설정
.env 파일에 AIRFLOW_UID=50000 를 추가한다.
리눅스에서는 내 컴퓨터의 사용자 ID와 컨테이너의 사용자 ID를 정확하게 맞춰주는 것이 중요하다.
하지만 윈도우의 Docker 환경에서는 파일 시스템 처리 방식이 달라,
Airflow Docker 환경에서 권장하는 기본값인 50000을 직접 지정해주는 것이 권장된다.

3. Airflow 데이터베이스 초기화
```bash
docker-compose up airflow-init
```

## 3단계: docker-compose.yaml 수정
Airflow 컨테이너가 우리 프로젝트의 collect_data.py 를 인식할 수 있도록 수정해야 한다.

x-airflow-common:
  &airflow-common
  # ... (생략) ...
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    - ./:/opt/airflow/project # 이 줄 추가

./:/opt/airflow/project 의 의미는 
'현재 프로젝트 폴더(.)를 Docker 컨테이너 안의 /opt/airflow/project 라는 경로에 마운트하기'
이다.

## 4단계: Airflow 실행 및 DAG 파일 경로 수정
1. Airflow와 관련 서비스를 백그라운드로 실행
```bash
docker-compose up -d
```

2. DAG 파일 수정
dags/challenger_data_dag.py 에서 bash_command를 절대경로로 수정한다.
bash_command="python /opt/airflow/project/collect_data.py", 


## 에러 수정
1. .env 파일 인코딩방식
.env 파일이 UTF-16 LE 라는 인코딩 방식으로 되어 있어, 에러가 발생했따.
=> Docker Compose는 .env파일을 UTF-8을 기준으로 읽으려고 하기 때문에, UTF-8 방식으로 저장하여 해결했다.

2. BashOperator 개선
```python
from airflow.operators.bash import BashOperator
```
의 방식은 구버전이라 WARNING 메시지가 발생한다.
=>
```python
from airflow.providers.standard.operators.bash import BashOperator
```
으로 개선하였다.