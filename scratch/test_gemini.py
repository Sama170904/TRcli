import urllib.request
import json
from pathlib import Path

env_file = Path(__file__).parent.parent / ".env"
api_key = ""
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            if k.strip() == "GEMINI_API_KEY":
                api_key = v.strip().strip("'\"")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

payload = {
    "contents": [
        {
            "parts": [{"text": "Dime 'Hola Copiloto' en español."}]
        }
    ]
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        print("\nResponse from Gemini 2.5 Flash API:")
        print(res_data["candidates"][0]["content"]["parts"][0]["text"])
except Exception as e:
    print(f"\nAPI Error: {e}")
