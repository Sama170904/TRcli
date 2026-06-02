import urllib.request
import json

url = "http://localhost:8085/api/chat"
payload = {"message": "¿Qué es un order block?"}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("API Response:")
        print(data.get("reply"))
except Exception as e:
    print(f"Error: {e}")
