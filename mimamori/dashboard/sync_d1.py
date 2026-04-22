import sqlite3
import os
import requests
import json
from datetime import datetime

# Configure settings from environment variables
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_DATABASE_ID = os.environ.get("CLOUDFLARE_DATABASE_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sensor_data.sqlite")

def get_latest_timestamp(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements';")
    if not cursor.fetchone():
        # Create table if it doesn't exist
        cursor.execute("CREATE TABLE measurements (timestamp TEXT PRIMARY KEY, temperature REAL);")
        conn.commit()
        return None

    cursor.execute("SELECT max(timestamp) FROM measurements;")
    row = cursor.fetchone()
    return row[0] if row else None

def fetch_d1_data(latest_timestamp):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/d1/database/{CLOUDFLARE_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Query D1 for new records
    if latest_timestamp:
        sql = "SELECT timestamp, temperature FROM measurements WHERE timestamp > ? ORDER BY timestamp ASC;"
        params = [latest_timestamp]
    else:
        sql = "SELECT timestamp, temperature FROM measurements ORDER BY timestamp ASC;"
        params = []
    
    data = {
        "params": params,
        "sql": sql
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    if not result.get("success"):
        raise Exception(f"D1 Query failed: {result.get('errors')}")
        
    return result["result"][0]["results"]

def main():
    if not all([CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_DATABASE_ID, CLOUDFLARE_API_TOKEN]):
        print("Error: Missing Cloudflare credentials. Please set CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_DATABASE_ID, and CLOUDFLARE_API_TOKEN.")
        return

    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    
    try:
        latest_timestamp = get_latest_timestamp(conn)
        print(f"Latest local timestamp: {latest_timestamp}")
        
        print("Fetching new data from Cloudflare D1...")
        new_records = fetch_d1_data(latest_timestamp)
        
        if not new_records:
            print("No new data to sync.")
            return
            
        print(f"Found {len(new_records)} new records. Syncing to local SQLite...")
        
        cursor = conn.cursor()
        for record in new_records:
            cursor.execute(
                "INSERT OR IGNORE INTO measurements (timestamp, temperature) VALUES (?, ?)",
                (record["timestamp"], record["temperature"])
            )
        
        conn.commit()
        print("Sync complete.")
        
    except Exception as e:
        print(f"Error during sync: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
