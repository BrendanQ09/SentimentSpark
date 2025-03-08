import time
import praw
import json
import os
from kafka import KafkaProducer
from textblob import TextBlob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka Config
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_SERVER = os.getenv("KAFKA_SERVER")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Reddit API Credentials
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD")
)

def get_reddit_posts():
    subreddit = reddit.subreddit("wallstreetbets")  # Target subreddit
    for post in subreddit.new(limit=50):  # Fetch latest 50 posts
        sentiment = TextBlob(post.title).sentiment.polarity
        sentiment_label = "positive" if sentiment > 0 else "negative" if sentiment < 0 else "neutral"

        data = {
            "post": post.title,
            "sentiment": sentiment_label,
            "timestamp": str(post.created_utc)
        }
        producer.send(KAFKA_TOPIC, data)
        print(f"Sent: {data}")

while True:
    get_reddit_posts()
    time.sleep(5)  # Fetch every 5 minutes
