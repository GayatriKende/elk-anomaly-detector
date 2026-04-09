#!/usr/bin/env python3

from elasticsearch import Elasticsearch
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime
import sys
import json

print(f"\n{'='*50}")
print(f"  Anomaly Detection Run: {datetime.now()}")
print(f"{'='*50}\n")

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Check connection
try:
    info = es.info()
    print(f"Connected to Elasticsearch: {info['version']['number']}")
except Exception as e:
    print(f"ERROR: Cannot connect to Elasticsearch: {e}")
    sys.exit(1)

def fetch_logs():
    """Fetch last 1 hour of logs from Elasticsearch"""
    print("Fetching logs from last 1 hour...")

    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-1h"}}}
                ],
                "must_not": [
                    {"exists": {"field": "anomaly_score"}}
                ]
            }
        },
        "size": 1000,
        "_source": [
            "response_time",
            "status_code",
            "log_level",
            "url",
            "client_ip",
            "@timestamp"
        ],
        "sort": [{"@timestamp": "desc"}]
    }

    try:
        result = es.search(index="app-logs-*", body=query)
        hits = result['hits']['hits']
        print(f"Found {len(hits)} log entries")

        records = []
        for hit in hits:
            src = hit['_source']
            records.append({
                '_id':           hit['_id'],
                '_index':        hit['_index'],
                'response_time': int(src.get('response_time', 0)),
                'status_code':   int(src.get('status_code', 200)),
                'is_error':      1 if src.get('log_level') in ['ERROR', 'WARNING'] else 0,
                'url':           src.get('url', '/'),
                'client_ip':     src.get('client_ip', ''),
                'timestamp':     src.get('@timestamp', '')
            })

        return pd.DataFrame(records)

    except Exception as e:
        print(f"ERROR fetching logs: {e}")
        return pd.DataFrame()

def detect_anomalies(df):
    """Run Isolation Forest anomaly detection"""

    if df.empty:
        print("No logs to analyze.")
        return

    print(f"\nRunning Isolation Forest on {len(df)} records...")

    # Features for ML model
    features = df[['response_time', 'status_code', 'is_error']].fillna(0)

    # Train Isolation Forest
    # contamination=0.05 means we expect 5% of data to be anomalous
    model = IsolationForest(
        contamination=0.05,
        n_estimators=100,
        random_state=42
    )

    # Predict: -1 = anomaly, 1 = normal
    df['anomaly_score']  = model.fit_predict(features)
    df['is_anomaly']     = df['anomaly_score'].apply(lambda x: 1 if x == -1 else 0)
    df['anomaly_reason'] = df.apply(get_anomaly_reason, axis=1)

    # Summary
    total     = len(df)
    anomalies = df[df['is_anomaly'] == 1]
    normal    = df[df['is_anomaly'] == 0]

    print(f"\nResults:")
    print(f"  Total logs analyzed : {total}")
    print(f"  Normal              : {len(normal)}")
    print(f"  Anomalies detected  : {len(anomalies)}")

    if not anomalies.empty:
        print(f"\nTop anomalies:")
        for _, row in anomalies.head(5).iterrows():
            print(f"  - {row['timestamp']} | "
                  f"response_time={row['response_time']}ms | "
                  f"status={row['status_code']} | "
                  f"reason={row['anomaly_reason']}")

    # Push results back to Elasticsearch
    push_results(df)

def get_anomaly_reason(row):
    """Human readable reason for anomaly"""
    reasons = []
    if row['response_time'] > 2000:
        reasons.append(f"high_response_time({row['response_time']}ms)")
    if row['status_code'] >= 500:
        reasons.append(f"server_error({row['status_code']})")
    if row['is_error'] == 1:
        reasons.append("error_log_level")
    return ", ".join(reasons) if reasons else "statistical_outlier"

def push_results(df):
    """Push anomaly results back to Elasticsearch"""
    print("\nPushing results to Elasticsearch...")

    anomalies = df[df['is_anomaly'] == 1]
    pushed    = 0

    for _, row in anomalies.iterrows():
        doc = {
            "original_timestamp" : row['timestamp'],
            "detected_at"        : datetime.utcnow().isoformat(),
            "response_time"      : row['response_time'],
            "status_code"        : row['status_code'],
            "url"                : row['url'],
            "client_ip"          : row['client_ip'],
            "is_error"           : bool(row['is_error']),
            "anomaly_reason"     : row['anomaly_reason'],
            "anomaly"            : True
        }

        try:
            es.index(index="anomalies", body=doc)
            pushed += 1
        except Exception as e:
            print(f"  Error pushing anomaly: {e}")

    print(f"Pushed {pushed} anomalies to 'anomalies' index")
    print(f"\nView in Kibana: Discover → Select 'anomalies' index")

if __name__ == '__main__':
    df = fetch_logs()
    detect_anomalies(df)
    print(f"\n{'='*50}")
    print(f"  Detection Complete")
    print(f"{'='*50}\n")
