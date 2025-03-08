import time
from kafka import KafkaProducer
import yfinance as yf
import json

KAFKA_TOPIC = "stock_prices"
KAFKA_SERVER = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

stocks = ["AAPL", "TSLA", "GOOGL", "AMZN"]
cache = {}

while True:
    for stock in stocks:
        stock_data = yf.Ticker(stock)
        price = stock_data.history(period="1d")["Close"].iloc[-1]

        if stock not in cache or cache[stock] != price:
            cache[stock] = price
            data = {
                "stock": stock,
                "price": price,
                "timestamp": time.time()
            }
            producer.send(KAFKA_TOPIC, data)
            print(f"Sent: {data}")

    time.sleep(60)  # Fetch every 60 seconds
