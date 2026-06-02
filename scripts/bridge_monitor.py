import json
import time
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
BRIDGE_FILE = VAULT_ROOT / "scratch" / "chat_bridge.json"

print("Bridge monitor started. Watching chat_bridge.json...", flush=True)

while True:
    try:
        if BRIDGE_FILE.exists():
            try:
                data = json.loads(BRIDGE_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # File might be partially written, wait a moment and try again
                time.sleep(0.2)
                continue
                
            if data.get("status") == "pending":
                request = data.get("request", "")
                print(f"\n[BRIDGE_PENDING] Request: {request}\n", flush=True)
                
                # Mark as processing so we don't trigger again for the same query
                data["status"] = "processing"
                BRIDGE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error in bridge monitor: {e}", flush=True)
    time.sleep(1)
