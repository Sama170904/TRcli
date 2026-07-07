import urllib.request
import re
import json
import sys

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
            
        desc = None
        # Try to find shortDescription in initial player response or HTML
        desc_match = re.search(r'"shortDescription":"(.*?)"', html)
        if desc_match:
            desc = desc_match.group(1).replace('\\n', '\n').replace('\\"', '"')
        else:
            match = re.search(r"ytInitialPlayerResponse\s*=\s*({.*?});", html)
            if not match:
                match = re.search(r"ytInitialPlayerResponse\s*=\s*({.*?})\s*</script>", html)
            if match:
                player_response = json.loads(match.group(1))
                desc = player_response.get("videoDetails", {}).get("shortDescription", None)
        
        if desc:
            results[vid] = desc
            print(f"{vid}: Successfully retrieved description")
        else:
            results[vid] = "Not found"
            print(f"{vid}: Description not found")
    except Exception as e:
        results[vid] = f"Error: {e}"
        print(f"{vid}: Error {e}")

with open("scratch/scraped_descriptions.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
