import streamlit as st
from kafka import KafkaConsumer
import json
import time
import pandas as pd
import datetime
import seaborn as sns
import matplotlib.pyplot as plt

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
        auto_offset_reset="latest",  # or "earliest" if you want historical data
        consumer_timeout_ms=2000,
    )
    messages = [msg.value for msg in consumer if msg.value]
    return messages

# Convert UNIX timestamp to a human-readable format
def convert_timestamp(ts):
    try:
        return datetime.datetime.fromtimestamp(float(ts))
    except Exception:
        return ts

# Sentiment to numeric mapping (for average sentiment chart)
SENTIMENT_MAP = {
    "positive": 1,
    "neutral": 0,
    "negative": -1
}

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
    
    # Convert and store a proper datetime
    if "timestamp" in df.columns:
        df["datetime"] = df["timestamp"].apply(convert_timestamp)
        # Create a human-readable time column
        df["readable_time"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Only display relevant columns in the data table
    st.subheader("Raw Data")
    # Show post, sentiment, and readable_time
    if all(col in df.columns for col in ["post", "sentiment", "readable_time"]):
        st.dataframe(df[["readable_time", "post", "sentiment"]])
    else:
        st.dataframe(df)  # fallback if columns are missing

    # --- Visualization 1: Sentiment Distribution Bar Chart ---
    if "sentiment" in df.columns:
        sentiment_counts = df["sentiment"].value_counts()
        st.subheader("Sentiment Distribution")
        st.bar_chart(sentiment_counts)

    # --- Visualization 2: Average Sentiment Over Time (Line Chart) ---
    if "datetime" in df.columns and "sentiment" in df.columns:
        # 1. Map sentiment to numeric scores
        df["sentiment_score"] = df["sentiment"].map({"positive": 1, "neutral": 0, "negative": -1})
        
        # 2. Group by hour and calculate the average sentiment
        hourly_sentiment = df.groupby(pd.Grouper(key="datetime", freq="1H"))["sentiment_score"].mean()

        # 3. Create a continuous date range from the earliest to the latest timestamp in your data
        if not hourly_sentiment.empty:
            full_range = pd.date_range(start=hourly_sentiment.index.min(),
                                    end=hourly_sentiment.index.max(),
                                    freq="1H")
            
            # 4. Reindex the grouped data to this continuous range and forward-fill missing hours
            hourly_sentiment = hourly_sentiment.reindex(full_range)
            hourly_sentiment.ffill(inplace=True)  # forward-fill to keep the last known sentiment

            # 5. Convert Series to DataFrame and rename index for clarity
            hourly_sentiment.index.name = "datetime"
            avg_sentiment_df = hourly_sentiment.reset_index(name="sentiment_score")
            
            st.subheader("Average Sentiment Over Time (Hourly, Forward-Filled)")
            st.line_chart(avg_sentiment_df.set_index("datetime"))
        else:
            st.warning("No data available to plot average sentiment.")


    # --- Visualization 3: Heatmap of Post Frequency by Day & Hour ---
    if "datetime" in df.columns:
        # Extract day of week (Mon=0) and hour
        df["day_of_week"] = df["datetime"].dt.day_name()
        df["hour"] = df["datetime"].dt.hour

        # Count how many posts per day/hour
        day_hour_counts = df.groupby(["day_of_week", "hour"]).size().reset_index(name="Count")

        # Convert to pivot table for heatmap
        # We want the rows to be days of week in order (Monday -> Sunday)
        # The built-in .dt.day_name() returns day names but not necessarily sorted
        # Let's create a custom day order:
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_hour_counts["day_of_week"] = pd.Categorical(day_hour_counts["day_of_week"], categories=day_order, ordered=True)

        pivot_table = day_hour_counts.pivot(index="day_of_week", columns="hour", values="Count").fillna(0)

        st.subheader("Heatmap: Posts by Day & Hour")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_table, cmap="YlOrRd", annot=True, fmt=".0f", ax=ax)
        ax.set_title("Posts by Day of Week and Hour")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("")
        st.pyplot(fig)

    # --- (Optional) Latest 10 Messages in a short list ---
    # Remove this if you don't want to show them again
    st.subheader("Latest Messages")
    latest_df = df.tail(10)
    for _, row in latest_df.iterrows():
        st.write(f"**{row.get('readable_time', '')}** - {row.get('post', '')} ({row.get('sentiment', '')})")
else:
    st.write("No messages available at the moment.")

# Auto-refresh the app every 60 seconds
time.sleep(60)
st.rerun()
