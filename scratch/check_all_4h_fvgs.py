import os
os.environ["SMC_CREDIT"] = "0"
import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc

df_1h = yf.download("MNQ=F", period="15d", interval="1h", progress=False)
if not df_1h.empty:
    df_1h.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_1h.columns]
    df_4h = df_1h.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    fvgs_4h = smc.fvg(df_4h)
    
    print("=== TODOS LOS FVGs 4H EN MNQ=F (ÚLTIMOS 15 DÍAS) ===")
    for idx, row in fvgs_4h.iterrows():
        date = df_4h.index[idx]
        fvg_val = row["FVG"]
        if fvg_val != 0 and not pd.isna(fvg_val):
            fvg_type = "Bullish" if fvg_val == 1 else "Bearish"
            mitigated = "Mitigado" if row["MitigatedIndex"] > 0 else "Activo"
            print(f"Fecha: {date.strftime('%Y-%m-%d %H:%M')} | {fvg_type} | Rango: {row['Bottom']:.2f} - {row['Top']:.2f} | Estado: {mitigated} (Mitigado en vela #{row['MitigatedIndex']})")
