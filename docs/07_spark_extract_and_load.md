# Spark로 데이터를 가공하고, 다시 S3에 저장

S3의 원본 데이터를 읽고 -> Spark로 가공하고 -> 다시 S3에 저장하는 
완전한 ETL 사이클 하나를 완성했다.

## 데이터 변환

지금까지 S3에서 데이터를 읽고, Spark 데이터 프레임으로 만들었다.
승률 '컬럼'을 새로 추가하고, 분석에 필요한 컬럼만 선택해서 새로운 데이터 프레임을 만든다.

```python
# process_data.py 파일의 일부

# ... (파일 상단 SparkSession 설정 부분은 동일) ...
# pyspark.sql.functions에서 col 함수를 추가로 import 합니다.
from pyspark.sql.functions import col

# ...

try:
    print(f"S3 경로에서 데이터를 읽습니다: {s3_path}")
    df = spark.read.option("multiLine", True).json(s3_path)

    print("데이터를 성공적으로 읽었습니다!")
    
    # --- 💡 데이터 변환(Transform) 단계 시작 ---
    print("\n--- 데이터 가공 시작 ---")
    
    # 1. 필요한 컬럼만 선택하고, 'winRate'라는 새로운 컬럼 추가
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

    print("데이터 가공 완료!")

    # --- 가공된 데이터 확인 ---
    print("\n--- 가공된 데이터 스키마 ---")
    processed_df.printSchema()

    print("\n--- 가공된 데이터 샘플 (상위 5개) ---")
    # 정렬 기능을 추가하여 LP가 높은 순으로 5명을 봅니다.
    processed_df.sort(col("leaguePoints").desc()).show(5)

except Exception as e:
    print(f"데이터 처리 중 에러가 발생했습니다: {e}")

finally:
    # ... (파일 하단 SparkSession 종료 부분은 동일) ...
```
주요 변경점은
- pyspark.sql.functions에서 col 함수를 가져왔다. 이는 데이터프레임의 컬럼을 지칭할 때 사용합니다.
- select()를 사용해 분석에 필요한 5개의 컬럼만 선택했다.
- withColumn()을 사용해 wins와 losses를 사용하여 새로운 winRate라는 컬럼을 만들었다.
- show()에 sort()를 사용하여 리그포인트가 높은 순서로 결과를 확인한다.

## 권한 문제 해결

프로젝트 폴더에서 spark라는 유저로 파일 내용을 쓰려고 하니 권한 문제가 발생하였다.

=> docker-compose.yaml에서 spark-master 부분에서 user:root를 추가하여 해결하였다.

```yaml
spark-master:
  image: apache/spark:3.5.7-python3
  user: root  # 권한 문제 해결
  environment:
    - SPARK_MODE=master
```

## Parquet 포맷 사용

데이터를 가공한 것을 그대로 다시 S3에 저장하는 것이 아니라 Parquet으로 변환하여 저장한다.

Parquet은 다음과 같은 장점들이 있다.
- 효율성: JSON이나 CSV 같은 텍스트파일 보다 훨씬 적은 용량을 차지하고, 데이터를 읽는 속도가 매우 빠르다.
- 구조 유지: 데이터의 스키마(컬럼 이름, 데이터 타입 등)를 파일 자체에서 저장하기 때문에, 데이터를 읽을 때 구조가 깨질 것을 걱정할 필요가 없다.
- 표준: Spark, Redshift, BigQuery 등 거의 모든 빅데이터 분석 시스템에서 표준처럼 사용된다.

