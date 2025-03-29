import time
import praw
import json
import os
from kafka import KafkaProducer
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Kafka Config
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_SERVER = os.getenv("KAFKA_SERVER")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# MongoDB Setup
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["stock_sentiment"]
mongo_collection = mongo_db["reddit_data"]

# Reddit API Credentials
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD")
)

# Load FinBERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

def get_finance_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    scores = torch.nn.functional.softmax(outputs.logits, dim=1)
    sentiment = scores.argmax().item()
    sentiment_label = ["negative", "neutral", "positive"][sentiment]
    return sentiment_label

def save_to_mongo_if_new(data):
    if not mongo_collection.find_one({"content": data["content"], "timestamp": data["timestamp"]}):
        mongo_collection.insert_one(data)
        return True
    return False

def get_reddit_posts():
    subreddit = reddit.subreddit("wallstreetbets")
    for post in subreddit.new(limit=50):
        sentiment_label = get_finance_sentiment(post.title)
        post_data = {
            "type": "post",
            "content": post.title,
            "sentiment": sentiment_label,
            "timestamp": str(post.created_utc)
        }
        if save_to_mongo_if_new(post_data):
            producer.send(KAFKA_TOPIC, post_data)
            print(f"Sent post: {post_data}")

        post.comments.replace_more(limit=0)
        for comment in post.comments.list()[:10]:
            comment_sentiment = get_finance_sentiment(comment.body)
            comment_data = {
                "type": "comment",
                "content": comment.body,
                "sentiment": comment_sentiment,
                "timestamp": str(comment.created_utc),
                "parent_post": post.id
            }
            if save_to_mongo_if_new(comment_data):
                producer.send(KAFKA_TOPIC, comment_data)
                print(f"Sent comment: {comment_data}")

while True:
    get_reddit_posts()
    time.sleep(300)
