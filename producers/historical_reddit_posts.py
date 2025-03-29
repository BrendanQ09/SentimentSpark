import time
import datetime
import praw
import json
import os
from kafka import KafkaProducer
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pymongo import MongoClient
from bson import ObjectId  # for custom encoding of ObjectId

print("✅ Script has started.")

# Custom JSON Encoder to handle ObjectId
class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Load environment variables
load_dotenv()

# Kafka Config - use the custom encoder in the value_serializer
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_SERVER = os.getenv("KAFKA_SERVER")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v, cls=MongoEncoder).encode('utf-8')
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
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        scores = torch.nn.functional.softmax(outputs.logits, dim=1)
        sentiment = scores.argmax().item()
        return ["negative", "neutral", "positive"][sentiment]
    except Exception as e:
        print(f"❌ Error in sentiment analysis: {e}")
        return "unknown"

def save_to_mongo_if_new(data):
    # Check for duplicates based on 'content' and 'timestamp'
    if not mongo_collection.find_one({"content": data["content"], "timestamp": data["timestamp"]}):
        mongo_collection.insert_one(data)
        return True
    return False

def get_reddit_posts():
    subreddit = reddit.subreddit("wallstreetbets")
    print("🔍 Fetching posts from wallstreetbets for the past day...")
    
    # Calculate UNIX timestamp for one day ago
    one_day_ago = int((datetime.datetime.utcnow() - datetime.timedelta(days=1)).timestamp())
    
    post_count = 0
    comment_count = 0

    # Loop over the newest posts; adjust limit as needed (e.g., 1000)
    for post in subreddit.new(limit=1000):
        # Stop processing if the post is older than one day
        if post.created_utc < one_day_ago:
            break

        try:
            sentiment_label = get_finance_sentiment(post.title)
        except Exception as e:
            print(f"❌ Error processing sentiment for post {post.id}: {e}")
            continue

        post_data = {
            "type": "post",
            "content": post.title,
            "sentiment": sentiment_label,
            "timestamp": str(post.created_utc)
        }
        if save_to_mongo_if_new(post_data):
            producer.send(KAFKA_TOPIC, post_data)
            print(f"✅ Sent post: {post.id}")
            post_count += 1
        else:
            print(f"🔄 Duplicate post skipped: {post.id}")

        try:
            post.comments.replace_more(limit=0)
        except Exception as e:
            print(f"❌ Error replacing comments for post {post.id}: {e}")
            continue

        # Process up to 10 comments per post, only if they're within the past day
        for comment in post.comments.list()[:10]:
            if comment.created_utc < one_day_ago:
                continue
            try:
                comment_sentiment = get_finance_sentiment(comment.body)
            except Exception as e:
                print(f"❌ Error processing sentiment for comment in post {post.id}: {e}")
                continue

            comment_data = {
                "type": "comment",
                "content": comment.body,
                "sentiment": comment_sentiment,
                "timestamp": str(comment.created_utc),
                "parent_post": post.id
            }
            if save_to_mongo_if_new(comment_data):
                producer.send(KAFKA_TOPIC, comment_data)
                print(f"✅ Sent comment: {comment.id} (post: {post.id})")
                comment_count += 1
            else:
                print(f"🔄 Duplicate comment skipped: {comment.id} (post: {post.id})")

    print(f"🎉 Finished fetching. Total posts sent: {post_count}, total comments sent: {comment_count}")

# Run the script once to pull posts from the past day
try:
    get_reddit_posts()
except Exception as e:
    print(f"❌ Error in get_reddit_posts: {e}")

print("✅ Script finished.")
