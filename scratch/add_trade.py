import json
from pathlib import Path

journal_path = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\journal.json")

# Load existing
with open(journal_path, "r", encoding="utf-8") as f:
    entries = json.load(f)

# Restore June 9 trade
if entries and entries[0]["id"] == "1781012520000":
    entries[0]["mae"] = "140.0"
    entries[0]["mfe"] = "532.0"

# New trade
new_entry = {
    "id": "1781101581000",
    "datetime": "2026-06-10T08:31",
    "instrument": "ES",
    "session": "NY AM KZ",
    "direction": "Long",
    "entry": "7352.00",
    "sl": "7351.25",
    "tp": "7370.00",
    "exit": "7370.00",
    "result": "Win",
    "rr": "24.00",
    "confluences": "Inverse FVG / inverse structure present; In Kill Zone (London / NY AM / PM); Buy-side / sell-side liquidity swept",
    "notes": "Long en MES en 7352.00 tras la volatilidad de apertura. Entrada gatillada por el iFVG formado tras el barrido de liquidez de mínimos. Salida en el objetivo de 7370.00 (+18 puntos, +$401.00 USD netos).",
    "mae": "0.0",
    "mfe": "0.0"
}

# Prepend
entries.insert(0, new_entry)

# Write back
with open(journal_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print("Restored June 9 and inserted June 10 trade successfully!")
