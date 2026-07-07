import sys
import re
import json
from curl_cffi import requests

video_ids = [
    "Uj6yXhPqTIg", # 45
    "75PiRQjxpQI", # 46
    "Na-rJyMP6cg", # 47
    "FfFt0L-NyDI", # 48
    "01nfxVrUUMg", # 49
    "AApR1hq6QQA", # 50
    "kadjhG_Zwog", # 51
    "9v86nWvCjiQ"  # 52
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

for vid in video_ids:
    url = f"https://www.youtube.com/watch?v={vid}"
    print(f"Fetching {vid}...")
    try:
        response = requests.get(url, headers=headers, impersonate="chrome120", timeout=10)
        if response.status_code != 200:
            print(f"{vid}: HTTP status {response.status_code}")
            continue
            
        html = response.text
        match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
        if not match:
            match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
            
        if not match:
            print(f"{vid}: ytInitialPlayerResponse not found")
            continue
            
        player_response = json.loads(match.group(1))
        video_details = player_response.get("videoDetails", {})
        title = video_details.get("title", "Unknown Title")
        print(f"ID: {vid} -> Title: {title}")
    except Exception as e:
        print(f"{vid}: Error: {e}")
