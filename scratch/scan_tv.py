import os
import sys
import json
import time
import subprocess
import shutil

mcp_cli = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
artifact_dir = r"C:\Users\rsama\.gemini\antigravity-cli\brain\13386512-7a18-48db-9191-4580543a5901"
os.makedirs(artifact_dir, exist_ok=True)

def run_tv(args):
    cmd = ["node", mcp_cli] + args
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"Error executing {args}: {res.stderr}")
        return None
    try:
        return json.loads(res.stdout)
    except Exception:
        return res.stdout.strip()

# Save initial state
init_state = run_tv(["state"])
print(f"Initial state: {init_state}")

symbols = ["CME_MINI:MES1!", "CME_MINI:MNQ1!"]
timeframes = ["240", "60", "30", "15", "5", "2"] # 4H, 1H, 30m, 15m, 5m, 2m

results = {}

for sym in symbols:
    results[sym] = {}
    print(f"Switching to symbol: {sym}")
    run_tv(["symbol", sym])
    time.sleep(2)
    
    for tf in timeframes:
        print(f"  Switching to timeframe: {tf}")
        run_tv(["timeframe", tf])
        time.sleep(4.0) # Wait for TV to load and draw
        
        # Get data
        boxes = run_tv(["data", "boxes"])
        lines = run_tv(["data", "lines"])
        labels = run_tv(["data", "labels"])
        ohlcv = run_tv(["ohlcv", "-s"])
        
        # Take screenshot
        out_name = f"{sym.replace(':', '_').replace('!', '')}_{tf}"
        ss = run_tv(["screenshot", "-o", out_name])
        
        ss_path = None
        if ss and isinstance(ss, dict) and ss.get("success"):
            ss_path = ss.get("file_path")
            # Copy to artifact dir
            if ss_path and os.path.exists(ss_path):
                dest = os.path.join(artifact_dir, f"{out_name}.png")
                shutil.copy2(ss_path, dest)
                print(f"    Screenshot saved and copied to: {dest}")
        
        results[sym][tf] = {
            "boxes": boxes,
            "lines": lines,
            "labels": labels,
            "ohlcv": ohlcv,
            "screenshot": f"{out_name}.png" if ss_path else None
        }

# Restore initial state
if init_state and isinstance(init_state, dict):
    print("Restoring initial state...")
    run_tv(["symbol", init_state.get("symbol")])
    time.sleep(1.5)
    run_tv(["timeframe", init_state.get("resolution")])

with open(os.path.join(artifact_dir, "tv_scan_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("Scan complete.")
