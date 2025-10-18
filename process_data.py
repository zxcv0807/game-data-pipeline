import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count

# AWS 자격 증명
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# S3 버킷 정보 
S3_BUCKET_NAME = 'zxcv0807-game-data-bucket'
S3_FILE_KEY = 'raw-data/challengers/challengers.json'

def main():
    print("Spark 세션을 시작합니다...")
    # SparkSession을 생성
    spark = SparkSession.builder \
        .appName("ChallengerDataProcessing") \
        .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY_ID) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()
    print("Spark 세션이 성공적으로 생성되었습니다.")

    s3_path = f"s3a://{S3_BUCKET_NAME}/{S3_FILE_KEY}"
    
    try:
        print(f"S3 경로에서 데이터를 읽습니다: {s3_path}")
        df = spark.read.option("multiLine", True).json(s3_path)
        print("데이터를 성공적으로 읽었습니다!")
        
        # --- 데이터 변환(Transform) 단계 ---
        print("\n--- 데이터 가공 시작 ---")
        processed_df = df.select(
            col("summonerName"),
            col("leaguePoints"),
            col("rank"),
            col("wins"),
            col("losses")
        ).withColumn(
            "winRate",
            col("wins") / (col("wins") + col("losses"))
        )
        print("기본 데이터 가공 완료!")

        # ---  데이터 집계(Aggregation) 단계 추가 ---
        print("\n--- 랭크별 평균 승률 및 LP 집계 시작 ---")
        # 'rank' 컬럼을 기준으로 그룹화하고, 각 그룹별 평균 계산
        agg_df = processed_df.groupBy("rank").agg(
            avg("winRate").alias("averageWinRate"), # 평균 승률 계산
            avg("leaguePoints").alias("averageLeaguePoints"), # 평균 LP 계산
            count("*").alias("numberOfPlayers") # 그룹별 플레이어 수 계산
        )
        print("데이터 집계 완료!")

        # --- 집계된 데이터 확인 ---
        print("\n--- 집계된 데이터 스키마 ---")
        agg_df.printSchema()
        print("\n--- 집계된 데이터 샘플 ---")
        agg_df.show() # 집계 결과는 보통 많지 않으므로 전체를 보여줍니다.

        # --- 가공된 데이터 S3에 저장(Load) 단계 시작 ---
        print("\n--- 가공된 데이터 S3에 저장 시작 ---")
        # 저장할 S3 경로 설정
        processed_s3_path = f"s3a://{S3_BUCKET_NAME}/processed-data/challengers/"
        # 데이터를 Parquet 포맷으로 S3에 저장
        # mode("overwrite"): 만약 같은 경로에 데이터가 이미 있다면 덮어쓰기
        processed_df.write.mode("overwrite").parquet(processed_s3_path)
        print(f"가공된 데이터가 S3 경로 '{processed_s3_path}'에 Parquet 포맷으로 저장되었습니다.")

        # ---  집계된 데이터 S3 CSV 저장 단계 추가 ---
        agg_s3_path = f"s3a://{S3_BUCKET_NAME}/aggregated-data/challengers-summary/"
        print(f"\n--- 집계된 요약 데이터 S3 CSV 저장 시작 ({agg_s3_path}) ---")
        # CSV로 저장할 때는 보통 하나의 파일로 합치는 것이 편리합니다.
        # repartition(1): 데이터를 하나의 파티션으로 합침
        # header=True: CSV 파일 첫 줄에 컬럼 이름 포함
        agg_df.repartition(1).write.mode("overwrite").option("header", True).csv(agg_s3_path)
        print("요약 데이터 CSV 저장 완료!")


    except Exception as e:
        print(f"데이터 처리 중 에러가 발생했습니다: {e}")

    finally:
        # SparkSession을 종료합니다.
        print("Spark 세션을 종료합니다.")
        spark.stop()

if __name__ == "__main__":
    main()