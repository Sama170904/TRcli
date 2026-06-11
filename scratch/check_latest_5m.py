import os
os.environ["SMC_CREDIT"] = "0"
import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc

df_5m = yf.download("MES=F", period="1d", interval="5m", progress=False).tail(10)
df_5m.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_5m.columns]
fvgs = smc.fvg(df_5m)
print("=== ÚLTIMAS VELAS 5M ===")
for idx, row in df_5m.iterrows():
    print(f"Hora: {idx.strftime('%H:%M')} | O: {row['open']:.2f} | H: {row['high']:.2f} | L: {row['low']:.2f} | C: {row['close']:.2f}")

print("\n=== FVGs 5M DETECTADOS ===")
for idx, row in fvgs.iterrows():
    if row["FVG"] != 0:
        fvg_type = "Bullish" if row["FVG"] == 1 else "Bearish"
        date_str = df_5m.index[idx].strftime('%H:%M')
        print(f"Hora: {date_str} | {fvg_type} | Bottom: {row['Bottom']:.2f} | Top: {row['Top']:.2f}")
