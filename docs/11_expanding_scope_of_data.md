# 데이터 수집 범위 확장

기존에는 챌린저 유저에 한해서만 데이터를 수집하였지만, 이를 다른 리그 티어어의 유저까지 확장하였다. 챌린저, 그랜드마스터, 마스터 유저로 확장하였다.

## 파일 수정

### collect_data.py
1. LEAGUES_TO_FETCH 에다가 챌린저, 그랜드마스터, 마스터의 API 주소들을 정의하였다.

2. tier라는 컬럼을 추가하여 각 플레이어 데이터에 어느 리그에서 왔는 지 명시하였다.

3. 챌린저와 그랜드마스터의 유저 수는 작지만, 마스터부터는 유저수가 많기 때문에, LP 기준 상위 100명만 수집하도록 샘플링 로직을 추가하였다.

4. S3의 파일명도 이제는 다른 리그까지 수집하기 때문에 challengers.json 대신 league_data.json으로 수정하였다.

### check_data_quality.py
S3_FILE_KEY에서 collect_data.py에서 수정한 것처럼 동일하게 수정한다.

### process_data.py
1. 마찬가지로 다른 두 파일에서 수정한 것처럼 S3_FILE_KEY에서 league_data.json로 수정한다.

2. groupby에서 tier를 추가해준다.


## trouble shooting

실행은 성공했지만 로그를 살펴보면, 정보 조회 실패: 429 에러가 굉장히 많이 보인다.
429에러는 Too Many Requests 라는 의미의 표준 에러이다. 
Riot Games 에서는 아래와 같이 api 요청 제한을 뒀는 데, 이를 확인하지 못했다.
Rate Limits
20 requests every 1 seconds(s)
100 requests every 2 minutes(s)

=> time.sleep()을 1.3초로 수정하여 api요청 제한을 준수하여 해결하였다.

