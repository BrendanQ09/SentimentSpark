import streamlit as st
from kafka import KafkaConsumer
import json
import time
import pandas as pd
import datetime

# Kafka Configuration
KAFKA_BROKER = "localhost:9092"
TOPIC = "stock_tweets"

# Safe JSON Deserializer
def safe_json_deserializer(x):
    try:
        return json.loads(x.decode("utf-8")) if x else None
    except json.JSONDecodeError:
        return None

# Function to get Kafka messages
def get_kafka_messages():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=safe_json_deserializer,
        auto_offset_reset="latest",
        consumer_timeout_ms=2000,
    )
    messages = [msg.value for msg in consumer if msg.value]
    return messages

# Convert UNIX timestamp to a human-readable format
def convert_timestamp(ts):
    try:
        return datetime.datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ts

# Streamlit UI setup
st.title("📊 Kafka Live Data Stream and Visualization")

# Initialize session state to store messages across reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fetch new messages from Kafka
new_messages = get_kafka_messages()
if new_messages:
    st.session_state.messages.extend(new_messages)

# Proceed if there are any messages
if st.session_state.messages:
    # Create a DataFrame from the messages
    df = pd.DataFrame(st.session_state.messages)
    
    # Process the timestamp if available
    if "timestamp" in df.columns:
        df["readable_time"] = df["timestamp"].apply(convert_timestamp)
        df["datetime"] = pd.to_datetime(df["timestamp"].astype(float), unit='s')
    
    # Display the raw data table
    st.subheader("Raw Data")
    st.dataframe(df)
    
    # Visualization 1: Sentiment Distribution Bar Chart
    if "sentiment" in df.columns:
        sentiment_counts = df["sentiment"].value_counts()
        st.subheader("Sentiment Distribution")
        st.bar_chart(sentiment_counts)
    
    # Visualization 2: Time Series of Message Counts (grouped by minute)
    if "datetime" in df.columns:
        # Group messages by minute and count them
        time_counts = df.groupby(pd.Grouper(key="datetime", freq="1Min")).size().reset_index(name='Count')
        st.subheader("Messages Over Time")
        st.line_chart(time_counts.set_index("datetime"))
    
    # Display the latest 10 messages in a more readable format
    st.subheader("Latest Messages")
    for _, row in df.tail(10).iterrows():
        st.write(f"**{row.get('readable_time', '')}** - {row.get('post', '')} ({row.get('sentiment', '')})")
else:
    st.write("No messages available at the moment.")

# Auto-refresh the app every 5 seconds
time.sleep(60)
st.rerun()
