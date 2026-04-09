#!/bin/bash
# Generates test traffic to Flask app

SERVER="http://localhost:5000"

echo "Generating normal traffic (50 requests)..."
for i in $(seq 1 50); do
    curl -s "$SERVER/" > /dev/null
    curl -s "$SERVER/api/data" > /dev/null
    sleep 0.3
done

echo "Generating anomaly traffic (high load)..."
for i in $(seq 1 10); do
    curl -s "$SERVER/load" > /dev/null
    sleep 1
done

echo "Generating error traffic..."
for i in $(seq 1 10); do
    curl -s "$SERVER/error" > /dev/null
    sleep 0.5
done

echo ""
echo "Done! Check Kibana at http://localhost:5601"
echo "Log file: $(ls -lh /home/ubuntu/elk-anomaly-detector/logs/)"
