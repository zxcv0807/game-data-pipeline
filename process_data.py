import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, lit
from pyspark.sql.window import Window

# AWS 자격 증명
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# --- PostgreSQL 연결 정보 추가 ---
POSTGRES_HOST = "postgres"
POSTGRES_PORT = "5432"
POSTGRES_DB = "airflow"
POSTGRES_USER = "airflow"
POSTGRES_PASSWORD = "airflow"
POSTGRES_DRIVER = "org.postgresql.Driver"
# S3 버킷 정보 
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'zxcv0807-game-data-bucket')
S3_FILE_KEY = 'raw-data/league_data/league_data.json'

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
            col("tier"),
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

        # ---  랭크별 평균 승률 및 LP 집계 ---
        print("\n--- 랭크별 평균 승률 및 LP 집계 시작 ---")
        agg_df = processed_df.groupBy("tier").agg(
            avg("winRate").alias("averageWinRate"), # 평균 승률 계산
            avg("leaguePoints").alias("averageLeaguePoints"), # 평균 LP 계산
            count("*").alias("numberOfPlayers") # 그룹별 플레이어 수 계산
        )
        print("랭크별 데이터 집계 완료!")
        agg_df.show()
        # --- 랭크 분포 계산 단계 추가 ---
        print("\n--- 랭크 분포 계산 시작 ---")

        # 1. 전체 플레이어 수 계산
        total_players = processed_df.count()
        print(f"전체 플레이어 수: {total_players}")

        # 2. 랭크별 플레이어 수 계산
        rank_counts_df = processed_df.groupBy("tier").agg(
            count("*").alias("numberOfPlayers")
        )

        # 3. 각 랭크별 비율 계산
        rank_distribution_df = rank_counts_df.withColumn(
            "totalPlayers", lit(total_players)
        ).withColumn(
            "percentage",
            (col("numberOfPlayers") / col("totalPlayers")) * 100
        )

        print("랭크 분포 계산 완료!")
        # --- 랭크 분포 데이터 확인 ---
        print("\n--- 랭크 분포 데이터 스키마 ---")
        rank_distribution_df.printSchema()

        print("\n--- 랭크 분포 데이터 ---")
        rank_distribution_df.show()

        # --- 가공된 데이터 S3에 저장(Load) 단계 시작 ---
        print("\n--- 가공된 데이터 S3에 저장 시작 ---")
        # 저장할 S3 경로 설정
        processed_s3_path = f"s3a://{S3_BUCKET_NAME}/processed-data/league_data/"
        # 데이터를 Parquet 포맷으로 S3에 저장
        processed_df.write.mode("overwrite").parquet(processed_s3_path)
        print(f"가공된 데이터가 S3 경로 '{processed_s3_path}'에 Parquet 포맷으로 저장되었습니다.")

        # ---  평균 집계 데이터 CSV 저장 ---
        agg_s3_path = f"s3a://{S3_BUCKET_NAME}/aggregated-data/league-summary/"
        print(f"\n--- 집계된 요약 데이터 S3 CSV 저장 시작 ({agg_s3_path}) ---")
        agg_df.repartition(1).write.mode("overwrite").option("header", True).csv(agg_s3_path)
        print("요약 데이터 CSV 저장 완료!")

        # --- 랭크 분포 데이터 CSV 저장 단계 추가 ---
        dist_s3_path = f"s3a://{S3_BUCKET_NAME}/aggregated-data/league-distribution/"
        print(f"\n--- 랭크 분포 데이터 S3 CSV 저장 시작 ({dist_s3_path}) ---")
        rank_distribution_df.repartition(1).write.mode("overwrite").option("header", True).csv(dist_s3_path)
        print("랭크 분포 데이터 CSV 저장 완료!")

        # --- 집계된 데이터를 PostgreSQL에 저장 ---
        print("\n--- 집계된 요약 데이터 PostgreSQL 저장 시작 ---")
        # PostgreSQL JDBC URL 구성
        jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        # 저장할 테이블 이름
        table_name = "league_summary_stats"

        # 데이터프레임을 PostgreSQL 테이블에 쓰기
        agg_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", table_name) \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", POSTGRES_DRIVER) \
            .mode("overwrite") \
            .save()
            
        print(f"집계된 데이터가 PostgreSQL '{POSTGRES_DB}' 데이터베이스의 '{table_name}' 테이블에 저장되었습니다.")


    except Exception as e:
        print(f"데이터 처리 중 에러가 발생했습니다: {e}")

    finally:
        # SparkSession을 종료합니다.
        print("Spark 세션을 종료합니다.")
        spark.stop()

if __name__ == "__main__":
    main()