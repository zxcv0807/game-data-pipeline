import boto3
import json
import os

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'zxcv0807-game-data-bucket')
S3_FILE_KEY = 'raw-data/challengers/challengers.json'

def check_data_quality():
    """
    S3에 적재된 원본 데이터의 품질을 검사합니다.
    하나라도 실패하면 Exception을 발생시켜 Airflow 작업을 중단시킵니다.
    """
    print(f"데이터 품질 검사를 시작합니다: {S3_BUCKET_NAME}/{S3_FILE_KEY}")
    s3_client = boto3.client('s3')

    # 1. 파일 존재 및 크기 검사
    try:
        response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_KEY)
        file_size = response['ContentLength']

        if file_size < 10:
            raise ValueError(f"파일이 너무 작습니다 (Size: {file_size}). 데이터가 없는 것으로 간주합니다.")
        print(f"[성공] 1. 파일 존재 및 크기 검사 (Size: {file_size})")

    except Exception as e:
        print(f"[실패] 1. 파일 찾기 실패: {e}")
        raise

    # 2. 데이터 내용(핵심 컬럼) 검사
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_KEY)
        data = json.loads(obj['Body'].read().decode('utf-8'))

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("데이터가 비어있거나 올바른 형식이 아닙니다.")

        # 첫 번째 레코드에 핵심 컬럼('puuid')이 있는지 확인
        first_record = data[0]
        if 'puuid' not in first_record:
            raise ValueError("핵심 컬럼 'puuid'가 없습니다.")

        print(f"[성공] 2. 데이터 내용 검사 (총 {len(data)} 레코드, 'puuid' 컬럼 확인)")

    except Exception as e:
        print(f"[실패] 2. 데이터 내용 읽기/검사 실패: {e}")
        raise

    print("데이터 품질 검사 통과!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'zxcv0807-game-data-bucket')
    check_data_quality()
