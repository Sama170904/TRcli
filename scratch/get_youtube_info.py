import urllib.request
import re
import json

video_ids = [
    "iobWSD-QPMU",
    "hYjufCzkp1A",
    "9flzlGowfgo",
    "GH3gtDeW-eQ",
    "SOG7uz4SPWw",
    "c06hD3gjX98",
    "U6-cfm34wDQ",
    "koi52lJVys0"
]

results = {}

for vid in video_ids:
    url = f"https://www.youtube.com/watch?v={vid}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            title_match = re.search(r"<title>(.*?)</title>", html)
            if title_match:
                title = title_match.group(1).replace(" - YouTube", "")
                results[vid] = title
                print(f"{vid}: {title}")
            else:
                results[vid] = "Unknown Title"
                print(f"{vid}: Title not found")
    except Exception as e:
        results[vid] = f"Error: {str(e)}"
        print(f"{vid}: Error {e}")

with open("scratch/scraped_titles.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
