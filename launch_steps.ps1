Write-Host "Starting MongoDB..."
Start-Process cmd.exe -ArgumentList `
    '/k', 
    '"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" --dbpath "C:\mongo-data\db"'
Start-Sleep -Seconds 10

Write-Host "Starting Zookeeper..."
Start-Process cmd.exe -ArgumentList `
    '/k', 
    'cd /d C:\kafka\kafka_2.12-3.9.0\bin\windows && zookeeper-server-start.bat ..\..\config\zookeeper.properties'
Start-Sleep -Seconds 10

Write-Host "Starting Kafka Broker..."
Start-Process cmd.exe -ArgumentList `
    '/k', 
    'cd /d C:\kafka\kafka_2.12-3.9.0\bin\windows && kafka-server-start.bat ..\..\config\server.properties'
Start-Sleep -Seconds 10

Write-Host "Starting Tweet Producer..."
Start-Process cmd.exe -ArgumentList `
    '/k', 
    'cd /d C:\Users\Owner\kafka-stock-sentiment\producers && python tweet_producer.py'
Start-Sleep -Seconds 5

Write-Host "Starting Stock Price Producer..."
Start-Process cmd.exe -ArgumentList `
    '/k', 
    'cd /d C:\Users\Owner\kafka-stock-sentiment\producers && python stock_price_producer.py'
Start-Sleep -Seconds 5

Write-Host "Starting Streamlit Dashboard..."
Start-Process cmd.exe -ArgumentList `
    '/k',
    'cd /d C:\Users\Owner\kafka-stock-sentiment\dashboard && streamlit run dashboard.py'
Start-Sleep -Seconds 5

Write-Host "Testing MongoDB connection..."
Start-Process cmd.exe -ArgumentList `
    '/k',
    'python -c "from pymongo import MongoClient; db = MongoClient()[\"stock_sentiment\"]; c = db[\"reddit_data\"].count_documents({}); print(f\"✅ MongoDB has {{c}} docs\" if c>0 else \"⚠️  No docs found\")"'
