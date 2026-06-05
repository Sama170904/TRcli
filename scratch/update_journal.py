import json
from pathlib import Path

journal_path = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\journal.json")

trade1 = {
    "id": "1780580460000",
    "datetime": "2026-06-04T09:41",
    "instrument": "ES",
    "session": "NY AM KZ",
    "direction": "Short",
    "entry": "7553.00",
    "sl": "7559.50",
    "tp": "7544.50",
    "exit": "7553.00",
    "result": "BE",
    "rr": "0.0",
    "confluences": "Inverse FVG / inverse structure present; In HTF premium / discount zone; At HTF PD array (OB / FVG / Breaker); In Kill Zone (London / NY AM / PM)",
    "notes": "Short en MES en 7553.00 tras mitigación de 1H/4H Bearish FVG y confirmación de 1m iFVG. El precio dio una reacción inicial bajista hasta 7551.00, pero se devolvió rápido debido a la fuerza del mercado que aún no completaba su barrida alcista, sacándome en Breakeven (BE) en 7553.00 a las 9:47 AM.",
    "mae": "0.0",
    "mfe": "8.0"
}

trade2 = {
    "id": "1780581000000",
    "datetime": "2026-06-04T09:50",
    "instrument": "NQ",
    "session": "NY AM KZ",
    "direction": "Short",
    "entry": "30259.00",
    "sl": "30268.00",
    "tp": "30187.50",
    "exit": "30268.00",
    "result": "Loss",
    "rr": "0.0",
    "confluences": "Inverse FVG / inverse structure present; At HTF PD array (OB / FVG / Breaker); In Kill Zone (London / NY AM / PM)",
    "notes": "Short en MNQ en 30259.00 tras toque rápido del borde inferior del 5m FVG. Entrada prematura (FOMO) antes de la mitigación profunda real del FVG de 5m y sin confirmación de SMT. Detenido en Stop Loss a 30268.00 (-$100.00 USD) mientras el precio subía a completar la mitigación real.",
    "mae": "36.0",
    "mfe": "156.0"
}

if journal_path.exists():
    try:
        entries = json.loads(journal_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading journal.json: {e}")
        entries = []
else:
    entries = []

# Prepend the new trades (trade2 first since it happened later, so the most recent is entries[0])
entries.insert(0, trade1)
entries.insert(0, trade2)

journal_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
print("journal.json updated successfully.")
