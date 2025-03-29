import streamlit as st
import pandas as pd
import datetime
import pymongo
import seaborn as sns
import matplotlib.pyplot as plt
import re
from collections import Counter
from wordcloud import WordCloud

# --- Additional Stopword Filtering Setup ---
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

# Start with NLTK's default English stopwords
stopwords_set = set(stopwords.words("english"))
# Add custom stopwords specific to your domain or that you find uninformative
custom_stopwords = {"wsb", "subreddit", "post", "comment", "like", "im", "ive", "amp"}
stopwords_set.update(custom_stopwords)

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["stock_sentiment"]
collection = db["reddit_data"]

# Retrieve all documents from the collection
docs = list(collection.find())

if docs:
    # Convert _id to string (since ObjectId is not JSON serializable)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    
    df = pd.DataFrame(docs)

    # Convert the 'timestamp' field (stored as a string) into a datetime object if available.
    if "timestamp" in df.columns:
        try:
            df["datetime"] = pd.to_datetime(df["timestamp"].astype(float), unit='s')
            df["readable_time"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            st.error(f"Error converting timestamps: {e}")

    st.title("📊 MongoDB Data Dashboard")

    st.subheader("Raw Data")
    st.dataframe(df)

    # --- Visualization 1: Sentiment Distribution Bar Chart ---
    if "sentiment" in df.columns:
        sentiment_counts = df["sentiment"].value_counts()
        st.subheader("Sentiment Distribution")
        st.bar_chart(sentiment_counts)

    # --- Visualization 2: Average Sentiment Over Time (Line Chart) ---
    if "datetime" in df.columns and "sentiment" in df.columns:
        SENTIMENT_MAP = {"positive": 1, "neutral": 0, "negative": -1}
        df["sentiment_score"] = df["sentiment"].map(SENTIMENT_MAP)

        # Group by hour
        hourly_sentiment = df.groupby(pd.Grouper(key="datetime", freq="1H"))["sentiment_score"].mean()
        if not hourly_sentiment.empty:
            full_range = pd.date_range(start=hourly_sentiment.index.min(),
                                       end=hourly_sentiment.index.max(),
                                       freq="1H")
            hourly_sentiment = hourly_sentiment.reindex(full_range)
            hourly_sentiment.ffill(inplace=True)
            hourly_sentiment.index.name = "datetime"
            avg_sentiment_df = hourly_sentiment.reset_index(name="sentiment_score")

            st.subheader("Average Sentiment Over Time (Hourly)")
            st.line_chart(avg_sentiment_df.set_index("datetime"))
        else:
            st.warning("No data available to plot average sentiment.")

    # --- Visualization 3: Heatmap of Post Frequency by Day & Hour ---
    if "datetime" in df.columns:
        df["day_of_week"] = df["datetime"].dt.day_name()
        df["hour"] = df["datetime"].dt.hour

        day_hour_counts = df.groupby(["day_of_week", "hour"]).size().reset_index(name="Count")

        # Define a custom day order
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_hour_counts["day_of_week"] = pd.Categorical(day_hour_counts["day_of_week"], categories=day_order, ordered=True)

        pivot_table = day_hour_counts.pivot(index="day_of_week", columns="hour", values="Count").fillna(0)

        st.subheader("Heatmap: Posts by Day & Hour")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_table, cmap="YlOrRd", annot=True, fmt=".0f", ax=ax)
        ax.set_title("Posts by Day of Week and Hour")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Day of Week")
        st.pyplot(fig)

    # --- Visualization 4: Key Trend Analysis ---
    if "content" in df.columns:
        st.subheader("Key Trend Analysis")
        
        # Function to preprocess text: remove punctuation and lower-case the words.
        def preprocess_text(text):
            return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()
        
        # Combine all post/comment content into one large string
        all_text = " ".join(df["content"].dropna().tolist())
        all_text = preprocess_text(all_text)
        
        # Split text into words
        words = all_text.split()
        
        # Remove words in the stopwords_set and ensure word length > 2
        words = [word for word in words if word not in stopwords_set and len(word) > 2]
        
        # Frequency distribution of words
        word_freq = Counter(words)
        
        # Define key terms you want to track; adjust as needed.
        key_terms = ['tesla', 'ipo', 'apple', 'amazon', 'google', 'microsoft']
        key_trends = {k: v for k, v in word_freq.items() if k in key_terms}
        
        st.write("**Key Trend Mentions:**", key_trends)
        
        # Generate and display a word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)
        st.subheader("Word Cloud of Mentions")
        fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
        ax_wc.imshow(wordcloud, interpolation='bilinear')
        ax_wc.axis("off")
        st.pyplot(fig_wc)

else:
    st.error("No data found in MongoDB.")
