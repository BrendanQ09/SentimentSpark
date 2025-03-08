from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, FloatType

KAFKA_SERVER = "localhost:9092"

spark = SparkSession.builder \
    .appName("StockSentimentAnalysis") \
    .master("local[*]") \
    .getOrCreate()

stock_schema = StructType() \
    .add("stock", StringType()) \
    .add("price", FloatType()) \
    .add("timestamp", StringType())

tweet_schema = StructType() \
    .add("tweet", StringType()) \
    .add("sentiment", StringType()) \
    .add("timestamp", StringType())

stock_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", "stock_prices") \
    .load()

stock_df = stock_df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"), stock_schema).alias("data")).select("data.*")

tweet_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", "stock_tweets") \
    .load()

tweet_df = tweet_df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"), tweet_schema).alias("data")).select("data.*")

query = stock_df.writeStream.outputMode("append").format("console").start()
query2 = tweet_df.writeStream.outputMode("append").format("console").start()

query.awaitTermination()
query2.awaitTermination()
