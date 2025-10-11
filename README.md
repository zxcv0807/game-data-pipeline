#  실시간 라이엇 게임즈즈 데이터 파이프라인 구축 프로젝트

이 프로젝트는 Riot Games API를 활용하여 실시간으로 게임 데이터를 수집하고, 클라우드 환경에서 처리 및 적재하여 분석 기반을 마련하는 데이터 파이프라인을 구축하는 것을 목표로 한다.

## 📌 프로젝트 목표

-   Python을 이용한 API 데이터 수집 스크립트 개발
-   수집된 원본 데이터를 AWS S3 데이터 레이크에 안정적으로 저장
-   전체 데이터 수집 과정을 Docker 컨테이너화하여 재현성 확보
-   Apache Airflow를 이용한 데이터 파이프라인 워크플로우 자동화 및 스케줄링

## ⚙️ 아키텍처

*간단한 아키텍처 다이어그램을 그려서 이미지로 추가하면 포트폴리오에 매우 효과적입니다.*

1.  **스케줄링**: Apache Airflow가 매일 정해진 시간에 데이터 수집 작업을 트리거합니다.
2.  **데이터 수집**: Python 스크립트가 Riot Games API를 호출하여 챌린저 랭크 유저의 `PUUID` 목록과 각 `PUUID`에 해당하는 소환사 이름을 수집합니다.
3.  **데이터 적재**: 수집된 데이터를 JSON 형태로 정리하여 AWS S3 버킷의 `raw-data` 영역에 저장합니다.
4.  **실행 환경**: 데이터 수집 스크립트와 Airflow는 모두 Docker 컨테이너 환경에서 실행되어 안정성과 이식성을 보장합니다.

## 🛠️ 기술 스택

-   **Language**: Python
-   **Cloud**: AWS S3
-   **Containerization**: Docker, Docker Compose
-   **Workflow Orchestration**: Apache Airflow


## 🚀 프로젝트 설정 및 실행 방법

### 사전 요구사항

-   Git
-   Docker & Docker Compose
-   AWS CLI

### 설치 및 실행

1.  **프로젝트 클론**
    ```bash
    git clone [https://github.com/Your-Username/game-data-pipeline.git](https://github.com/Your-Username/game-data-pipeline.git)
    cd game-data-pipeline
    ```

2.  **환경 변수 설정**
    프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 채워주세요.
    ```
    RIOT_API_KEY="RGAPI-your-riot-api-key"
    AIRFLOW_UID=50000
    ```

3.  **AWS CLI 설정**
    아래 명령어를 실행하고 발급받은 AWS Access Key와 Secret Key를 입력하세요.
    ```bash
    aws configure
    ```

4.  **Airflow 초기화 및 실행**
    ```bash
    # Airflow DB 초기화 (최초 1회만 실행)
    docker-compose up airflow-init

    # Airflow 모든 서비스 실행
    docker-compose up -d
    ```

5.  **Airflow DAG 활성화**
    -   웹 브라우저에서 `http://localhost:8080`으로 접속합니다. (ID/PW: airflow)
    -   `collect_challenger_data_daily` DAG의 토글 버튼을 켜서 활성화합니다.
    -   ▶️ (재생) 버튼을 눌러 DAG를 수동으로 실행할 수 있습니다.

## ✅ 현재까지의 진행 상황

-   [x] Riot Games API 데이터 수집 스크립트 작성 (`PUUID`, 소환사 이름)
-   [x] 수집 데이터를 JSON 파일로 저장하는 기능 구현
-   [x] `boto3`를 이용해 AWS S3에 직접 업로드하는 기능 구현
-   [x] 데이터 수집 스크립트 Docker 컨테이너화 준비 완료
-   [x] Docker Compose를 이용한 로컬 Airflow 환경 구축
-   [x] Airflow DAG를 통해 데이터 수집 스크립트 자동 실행 기능 구현

