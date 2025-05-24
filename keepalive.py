# keepalive.py
import time
import requests
from datetime import datetime

BOT_URL = "https://meowbot-vxai.onrender.com"  # Replace with your real Render URL

def ping():
    try:
        response = requests.get(BOT_URL)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ Ping successful!")
        else:
            print(f"[{datetime.now()}] ❌ Ping failed: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ping error: {e}")

while True:
    ping()
    time.sleep(10 * 60)  # Wait 14 minutes
