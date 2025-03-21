# Start Zookeeper
Start-Process cmd.exe -ArgumentList '/k cd /d C:\kafka\kafka_2.12-3.9.0\bin\windows && zookeeper-server-start.bat ..\..\config\zookeeper.properties'
Start-Sleep -Seconds 10

# Start Kafka Broker
Start-Process cmd.exe -ArgumentList '/k cd /d C:\kafka\kafka_2.12-3.9.0\bin\windows && kafka-server-start.bat ..\..\config\server.properties'
Start-Sleep -Seconds 10

# Start Tweet Producer
Start-Process cmd.exe -ArgumentList '/k cd /d C:\Users\Owner\kafka-stock-sentiment\producers && python tweet_producer.py'

# Start Stock Price Producer
Start-Process cmd.exe -ArgumentList '/k cd /d C:\Users\Owner\kafka-stock-sentiment\producers && python stock_price_producer.py'

# OPTIONAL: Start Streamlit Dashboard (if you want it to launch automatically)
Start-Process cmd.exe -ArgumentList '/k cd /d C:\Users\Owner\kafka-stock-sentiment\dashboard && streamlit run dashboard.py'
