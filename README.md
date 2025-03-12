# 📊 Kafka Stock Sentiment Dashboard

## 🚀 Overview
A **real-time dashboard** for stock-related tweets using **Kafka & Streamlit**. Tweets are analyzed for sentiment (`positive`, `neutral`, `negative`) and visualized dynamically.

## 🛠 Features
- **🔄 Live Kafka Streaming** – Reads tweets from `stock_tweets` topic.
- **📊 Sentiment Analysis** – Bar chart for sentiment distribution.
- **📈 Sentiment Over Time** – Line chart (forward-filled to prevent gaps).
- **🔥 Tweet Frequency Heatmap** – Posts by **day & hour**.
- **📜 Latest Tweets** – Displays the most recent messages.

## ⚡ Setup
1️⃣ Install Dependencies
pip install -r requirements.txt

2️⃣ Start Kafka & Zookeeper
C:\kafka\bin\windows\zookeeper-server-start.bat C:\kafka\config\zookeeper.properties
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\server.properties

3️⃣ Create Kafka Topic
C:\kafka\bin\windows\kafka-topics.bat --create --topic stock_tweets --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

4️⃣ Start Producer & Streamlit
python producers/tweet_producer.py  # Send test tweets
streamlit run app.py  # Start dashboard

🎯 Next Steps
🚨 Add alerts for sentiment spikes.
📡 Integrate real Twitter API.
🏆 Improve ML sentiment accuracy.
