import os
from pyspark.sql import SparkSession

# AWS 자격 증명을 환경 변수에서 가져옵니다.
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# S3 버킷 정보 (본인 것으로 수정)
S3_BUCKET_NAME = 'zxcv0807-game-data-bucket'
S3_FILE_KEY = 'raw-data/challengers/challengers.json'

def main():
    print("Spark 세션을 시작합니다...")

    # SparkSession을 생성합니다.
    # S3 연동을 위한 필수 라이브러리(jar)들을 포함시킵니다.
    spark = SparkSession.builder \
        .appName("ChallengerDataProcessing") \
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY_ID) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

    print("Spark 세션이 성공적으로 생성되었습니다.")

    # S3에서 JSON 파일을 읽어 DataFrame으로 만듭니다.
    s3_path = f"s3a://{S3_BUCKET_NAME}/{S3_FILE_KEY}"
    
    try:
        print(f"S3 경로에서 데이터를 읽습니다: {s3_path}")
        df = spark.read.option("multiLine", True).json(s3_path)

        print("데이터를 성공적으로 읽었습니다!")
        
        # 데이터의 스키마(구조)를 출력합니다.
        print("--- 데이터 스키마 ---")
        df.printSchema()

        # 상위 5개의 데이터를 샘플로 출력합니다.
        print("--- 데이터 샘플 (상위 5개) ---")
        df.show(5)

    except Exception as e:
        print(f"데이터 처리 중 에러가 발생했습니다: {e}")

    finally:
        # SparkSession을 종료합니다.
        print("Spark 세션을 종료합니다.")
        spark.stop()

if __name__ == "__main__":
    main()