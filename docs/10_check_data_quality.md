# 데이터 품질 검사 추가
데이터의 수집과 처리 사이에서 수집한 데이터의 품질(데이터의 존재, 크기)를 확인하는 스크립트를 추가한다.

## plugins 폴더 내에 check_data_quality.py 스크립트 추가

1. 파일의 크기가 너무 작아서 제대로 수집이 안됐거나, 파일이 존재하지 않는다면 에러를 발생시키는 스크립트를 작성했다.
2. 데이터의 형식이 json 리스트 형식인지 확인한다.
3. 항상 사용하던 레코드인 'puuid'가 있는 지 확인한다.

이 중 하나라도 실패하면 스크립트는 예외를 발생시켜 Airflow DAG를 즉시 중단시킨다. 비정상적인 데이터가 하류의 Spark 처리 단계로 넘어가는 것을 차단한다.

## Trouble Shooting
check_data_quality.py 파일을 최상위폴더에 위치시키면 Airflow가 check_data_quality.py파일을 인식하지 못해서 에러가 발생한다.
=> Airflow가 인식할 수 있는 plugins 폴더아래로 check_data_quality.py파일을 이동시켜 ModuleNotFoundError를 해결하였다.
