import os
import json

results_path = r"C:\Users\rsama\.gemini\antigravity-cli\brain\13386512-7a18-48db-9191-4580543a5901\tv_scan_results.json"

if not os.path.exists(results_path):
    print("Results file not found.")
    exit(1)

with open(results_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Let's extract 2m bars for MES and MNQ
mes_2m = data.get("CME_MINI:MES1!", {}).get("2", {}).get("ohlcv", {})
mnq_2m = data.get("CME_MINI:MNQ1!", {}).get("2", {}).get("ohlcv", {})

print("MES 2m success:", isinstance(mes_2m, dict) and mes_2m.get("success"))
print("MNQ 2m success:", isinstance(mnq_2m, dict) and mnq_2m.get("success"))

# If they contain bars, let's look at them
mes_bars = mes_2m.get("bars", []) if isinstance(mes_2m, dict) else []
mnq_bars = mnq_2m.get("bars", []) if isinstance(mnq_2m, dict) else []

print(f"MES bars count: {len(mes_bars)}")
print(f"MNQ bars count: {len(mnq_bars)}")

if len(mes_bars) > 0 and len(mnq_bars) > 0:
    # Let's align them by timestamp (or index if they are already aligned)
    # Print the last 10 bars for comparison
    n = min(len(mes_bars), len(mnq_bars), 15)
    for i in range(-n, 0):
        m_bar = mes_bars[i]
        q_bar = mnq_bars[i]
        # Compare time
        m_time = m_bar.get("time")
        q_time = q_bar.get("time")
        print(f"Index {i}: Time MES={m_time} Low={m_bar.get('low')} Close={m_bar.get('close')} | Time MNQ={q_time} Low={q_bar.get('low')} Close={q_bar.get('close')}")
