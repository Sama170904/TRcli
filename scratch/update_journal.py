import json
import os
import shutil

# 1. Copy screenshot
src_screenshot = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\screenshots\tv_chart_2026-06-11T13-53-40-493Z.png"
dst_screenshot = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\imagenes\2026-06-11_chart.png"
try:
    shutil.copy(src_screenshot, dst_screenshot)
    print("Screenshot copied successfully.")
except Exception as e:
    print(f"Error copying screenshot: {e}")

# 2. Add to journal.json
journal_path = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\journal.json"
with open(journal_path, "r", encoding="utf-8") as f:
    journal = json.load(f)

new_trade = {
    "id": "1781185440000",
    "datetime": "2026-06-11T08:44",
    "instrument": "NQ",
    "session": "NY AM KZ",
    "direction": "Long",
    "entry": "28747.00",
    "sl": "28651.00",
    "tp": "28849.00",
    "exit": "28849.00",
    "result": "Win",
    "rr": "1.06",
    "confluences": "Inverse FVG / inverse structure present; At HTF PD array (OB / FVG / Breaker); In Kill Zone (London / NY AM / PM); HTF market structure bias confirmed",
    "notes": "Long en NQ en 28747.00 tras retesteo de 2m iFVG formado luego de tocar el nivel clave ifl 1h-dl. Salida en el take profit programado de 28849.00 (+102 puntos, +$458.00 USD netos). Cuenta en $52,706.00 USD."
}

# Check if already added
if not any(t["id"] == new_trade["id"] for t in journal):
    journal.insert(0, new_trade)
    with open(journal_path, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
    print("Journal.json updated successfully.")
else:
    print("Trade already exists in journal.json.")

# 3. Create session file in bitacoras/2026-06-11_session.md
session_md = """---
title: "Sesión 2026-06-11"
tags: [session, journal, autopsy]
created: 2026-06-11 08:44
pnl: 458.00
trades_count: 1
result: "WIN"
---

# 📅 BITÁCORA DE TRADING — 11 de Junio de 2026
**Pre-Trade Link:** [[2026-06-11_pre_trade_MNQ]]

## 📊 RESUMEN GENERAL DE LA SESIÓN
- **Resultado Neto:** `+$458.00 USD`
- **Trades Realizados:** `1`
- **Resultado:** `WIN`
- **Contexto de Cuenta Fondeada (Eval):**
  * Balance Actual: `$52,706.00 USD` (al 11/06/2026)
  * Objetivo de Beneficio: `$53,000.00 USD`
  * Distancia al Objetivo: `-$294.00 USD` (para alcanzar $53,000)
  * Días Hábiles Restantes: `5 días`

---

## 🖼️ CAPTURA DE PANTALLA
![Gráfico de la Sesión del 2026-06-11](../imagenes/2026-06-11_chart.png)

---

## 🔍 ANÁLISIS ESTRUCTURAL DE TEMPORALIDADES (TOP-DOWN)
### 1. Temporalidades Mayores (HTF: 4h / 1h)
- **Bias:** Bearish 🔴 | El sesgo macro en 1H era bajista, pero el precio cotizaba en una zona de descuento profundo (Discount), propiciando un rebote alcista.
- **Narrativa:** A pesar del bias bajista macro, la llegada al nivel de soporte institucional de la temporalidad diaria y de 1 hora (`ifl 1h-dl`) frenó la caída y dio la base para un rebote largo de alta precisión.

### 2. Temporalidades Intermedias (30m / 15m)
- **Zonas clave (POIs):** Reacción alcista limpia inmediatamente tras testear el nivel clave `ifl 1h-dl` en la zona de `28635.79`.

### 3. Temporalidad de Ejecución (5m / 2m / 1m)
- **Gatillo / Desplazamiento:** Se generó una reversión en la microestructura con un desplazamiento alcista fuerte que invalidó un FVG bajista en la temporalidad de 2 minutos, creando un **iFVG alcista (2m)**. Se ingresó al mercado en el retesteo del iFVG en `28747.00`.

---

## 📈 REPORTE DETALLADO DE LOS TRADES

### 🟢 TRADE #1: Long en NQ (Micro E-mini Nasdaq-100)
- **Entrada:** `28747.00` (8:44 AM local / 9:44 AM NY Time)
- **Exit:** `28849.00`
- **SL:** `28651.00` (Riesgo: 96 points)
- **MAE:** `0.0 ticks` (Entrada de precisión absoluta)
- **MFE:** `458.0 ticks` (102 puntos a favor, alcanzando y superando el TP)
- **Resultado:** `WIN (+$458.00 USD)`
- **Relación R:R:** **1.06:1**
- **Notas:** Entrada en la formación del iFVG de 2m tras testear el nivel clave `ifl 1h-dl`. La ejecución fue disciplinada y la salida se realizó de forma automática al alcanzar el objetivo estipulado en `28849.00`.

---

## 🧠 LECCIONES DE LA SESIÓN
1. **Confiar en los Niveles Institucionales:** El nivel de soporte de temporalidad mayor (`ifl 1h-dl`) sirvió como un excelente suelo, demostrando que incluso con un bias macro bajista, las compras en zonas de descuento extremo son de alta probabilidad si el gatillo es claro.
2. **Uso del iFVG de 2m:** Esperar a que el precio rompa la estructura bajista en la temporalidad menor y configure el iFVG evitó entrar a ciegas en la caída libre.
3. **Respetar la Gestión:** Salir en el TP programado consolida las ganancias y mantiene la disciplina rumbo al objetivo final de la cuenta de evaluación.
"""

session_path = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\bitacoras\2026-06-11_session.md"
with open(session_path, "w", encoding="utf-8") as f:
    f.write(session_md)
print("Session md created.")

# 4. Update dashboard.md
dashboard_path = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\dashboard.md"
with open(dashboard_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("* **Balance Actual:** `$52,248.00 USD` (al 10/06/2026)", "* **Balance Actual:** `$52,706.00 USD` (al 11/06/2026)")
content = content.replace("* **Distancia al Objetivo:** `+$752.00 USD`","* **Distancia al Objetivo:** `-$294.00 USD` (para alcanzar $53,000)")
content = content.replace("* **Días Hábiles Restantes:** `6 días`","* **Días Hábiles Restantes:** `5 días`")
content = content.replace("* **Balance Neto Total (Bitácora):** `+$2,825.00 USD`","* **Balance Neto Total (Bitácora):** `+$3,283.00 USD`")
content = content.replace("* **Total Sesiones Operadas:** `10`","* **Total Sesiones Operadas:** `11`")
content = content.replace("* **Sesiones Ganadoras (Win):** `6` (60.0% de efectividad de sesión)","* **Sesiones Ganadoras (Win):** `7` (63.6% de efectividad de sesión)")
content = content.replace("* **Total Trades Ejecutados:** `14`","* **Total Trades Ejecutados:** `15`")

old_winners = "*Trades Ganadores:* `8` (Trade #2 28/05: Parcial, Trade #3 28/05: TP Completo, Trade #1 02/06: TP Completo, Trade #1 03/06: BE+ de protección, Trade #1 05/06: TP Completo de 115 puntos, Trade #1 08/06: TP Completo de 20 puntos en MES, Trade #1 09/06: TP Completo de 133 puntos en NQ, Trade #1 10/06: TP Completo de 18 puntos en MES)"
new_winners = "*Trades Ganadores:* `9` (Trade #2 28/05: Parcial, Trade #3 28/05: TP Completo, Trade #1 02/06: TP Completo, Trade #1 03/06: BE+ de protection, Trade #1 05/06: TP Completo de 115 puntos, Trade #1 08/06: TP Completo de 20 puntos en MES, Trade #1 09/06: TP Completo de 133 puntos en NQ, Trade #1 10/06: TP Completo de 18 puntos en MES, Trade #1 11/06: TP Completo de 102 puntos en NQ)"
content = content.replace(old_winners, new_winners)

content = content.replace("* **Win Rate de Trades:** `57.1%` (8/14)","* **Win Rate de Trades:** `60.0%` (9/15)")

old_row = "| **10/06/2026** | Miércoles | **+$401.00** | 1 | 🟢 WIN | [Bitácora 10-06-2026](file:///C:/Users/rsama/Documents/proyecto-geminicli/trading-journal/bitacoras/2026-06-10_session.md) |"
new_row = "| **11/06/2026** | Jueves | **+$458.00** | 1 | 🟢 WIN | [Bitácora 11-06-2026](file:///C:/Users/rsama/Documents/proyecto-geminicli/trading-journal/bitacoras/2026-06-11_session.md) |\n" + old_row
content = content.replace(old_row, new_row)

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard updated successfully.")
