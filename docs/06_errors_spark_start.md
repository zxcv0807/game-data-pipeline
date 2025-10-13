# Spark를 시작하다가 생긴 에러들

## 응답 속도
```bash
docker-compose up -d
```
를 통해 실행하면 에러가 발생하지만, 실제로 
```bash
docker-compose logs airflow-apiserver
```
를 통해 로그를 확인해보면 정상적으로 응답하고 있다.
Docker가 응답이 너무 느려 unhealty라고 판단하여 에러메시지를 보낸 것이다.
=> docker-compose.yaml 파일에서 healthcheck 설정에서 timeout과 start_period를 넉넉하게 설정하여 해결하였다.

## spark-master 컨테이너 에러
```bash
docker-compose up -d
docker-compose ps
```
를 실행하면 spark-master의 상태가 아예 보이지 않았다. 
```bash
docker-compose logs spark-master
```
로 로그를 확인해 해결하려했지만, 아무런 결과가 보이지 않았다. 이것은 spark-master가 서비스를 시작조차 하지 못했다는 의미이다.
제미나이는 들여쓰기 문제나 .env환경변수 설정이 안됐을 확률이 크다고 했지만 그렇지 않았다.

=> 그래서 Spark 서비스만 단독 실행하여 테스트를 진행했다.
1. docker-compose.spark-test.yaml 파일 안에서 entrypoint: tail -f /dev/null 를 통해 계속 켜져있게 했다.
```YAML
services:
  spark-master:
    image: apache/spark:3.5.7-python3
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark-master
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./:/opt/spark/work-dir
    ports:
      - "8080:8080"
      - "7077:7077"
    entrypoint: tail -f /dev/null
```

2. 컨테이너 내부 접속 및 에러 확인
```bash
# 컨테이너 내부 셸 실행
docker-compose -f docker-compose.spark-test.yaml exec spark-master bash
# 원래 실행 스크립트 수동 실행
/opt/docker/bin/entrypoint.sh
```
결과는 파일이나 디텍토리가 없다고 나왔다. 이는 스크립트 경로가 잘못되었다는 것이다.

3. 올바른 스크립트 경로 찾기
```bash
ls -l /opt/spark/bin
```
결과 중에서 Spark Master를 시작시키는 실제 명령어는 spark-class 이다.
```bash
/opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
```
를 통해 직접 실행하면 에러가 생기는 것이 아닌 성공 메시지를 보게 되었다.

apache/spark Docker 이미지의 기본 entrypoint 스크립트는 우리 환경에서 제대로 작동하지 않아 컨테이너를 즉시 종료 시켰다.
하지만 컨테이너의 핵심 프로그램 자체는 아무 문제가 없다는 것을 알게되었다.

=> command를 직접 지정하여 해결하였다.
```yaml
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
```
를 추가하여 실제로 테스트 파일에서 잘 작동하는 것을 확인하였고, 원래 파일에도 적용하여 성공적으로 작동하는 것을 확인하였다.