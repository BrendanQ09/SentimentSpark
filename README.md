# 📊 Kafka Stock Sentiment Dashboard

## 🚀 Overview
A **real-time dashboard** for stock-related sentiment analysis powered by **Kafka, MongoDB & Streamlit**. Data (e.g., tweets or Reddit posts) is analyzed for sentiment (`positive`, `neutral`, `negative`) and visualized dynamically. The system automatically collects data daily, stores it in MongoDB, and then displays key insights including trend detection using word clouds.

## 🛠 Features
- **🔄 Live Kafka Streaming & Daily Data Collection**  
  - Producers send data (tweets or Reddit posts) to a Kafka topic.
  - A scheduled task collects and stores data in MongoDB daily.
- **📊 Sentiment Analysis**  
  - Displays sentiment distribution via bar charts.
- **📈 Sentiment Over Time**  
  - Line charts show average sentiment over time (hourly, with forward-filling to prevent gaps).
- **🔥 Frequency Heatmap**  
  - Visualizes post frequency by day of the week and hour.
- **📝 Trend Analysis**  
  - Generates a word cloud that highlights key trends (e.g., mentions of "Tesla", "IPO", etc.) using advanced stopword filtering.

## ⚡ Setup

### 1. Install Dependencies
Run:
```bash
pip install -r requirements.txt
``` 
### 2. Start Kafka & Zookeeper
Launch Kafka and Zookeeper (adjust paths as necessary):
```bash
C:\kafka\bin\windows\zookeeper-server-start.bat C:\kafka\config\zookeeper.properties
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\server.properties
```
### 3. Create Kafka Topic
For example, to create a topic named stock_tweets:
```bash
C:\kafka\bin\windows\kafka-topics.bat --create --topic stock_tweets --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### 4. Data Producer
Start the Producer Script:
Run your data producer to fetch and process data (e.g., tweets or Reddit posts) and store it in MongoDB:
```bash
python producers/tweet_producer.py    # For Twitter data
```
# or
```bash
python producers/historical_reddit_posts.py   # For Reddit data
```
Automate Daily Runs:
Schedule your producer script to run daily using Windows Task Scheduler:

Create a batch file (e.g., run_producer.bat) containing:

batch
Copy
```bash
"C:\Users\Owner\AppData\Local\Programs\Python\Python310\python.exe" "c:\Users\Owner\kafka-stock-sentiment\producers\historical_reddit_posts.py"
pause
```

### 5. MongoDB
Ensure MongoDB is running continuously. The producer script stores data in the stock_sentiment database (e.g., collection reddit_data).

### 6. Dashboard
Launch your Streamlit dashboard to visualize the data:

```bash
streamlit run app.py
```

🎯 Next Steps
🚨 Add alerts for sentiment spikes.

📡 Integrate a live Twitter API for real-time tweet collection.

🤖 Enhance sentiment analysis accuracy with improved ML models.

⏰ Further automate data collection and processing workflows.

📝 Additional Enhancements
Trend Analysis with Word Cloud:
The dashboard includes a word cloud that uses NLTK’s stopword list (plus custom stopwords) to filter out common filler words. This helps highlight key emerging trends (e.g., "Tesla", "IPO").

Duplicate Prevention:
Data is checked for duplicates before insertion into MongoDB, ensuring that rerunning the producer doesn't result in redundant entries.
