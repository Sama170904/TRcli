import os
os.environ["SMC_CREDIT"] = "0"
import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc

df_d = yf.download("MNQ=F", period="6mo", interval="1d", progress=False)
if not df_d.empty:
    df_d.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_d.columns]
    fvgs_d = smc.fvg(df_d)
    
    # Imprimir todos los FVGs detectados en los últimos 45 días
    print("=== TODOS LOS FVGs DIARIOS EN MNQ=F (ÚLTIMOS 60 DÍAS) ===")
    for idx, row in fvgs_d.iterrows():
        date = df_d.index[idx]
        if (pd.Timestamp.now() - date).days <= 60:
            fvg_val = row["FVG"]
            if fvg_val != 0 and not pd.isna(fvg_val):
                fvg_type = "Bullish" if fvg_val == 1 else "Bearish"
                mitigated = "Mitigado" if row["MitigatedIndex"] > 0 else "Activo"
                print(f"Fecha: {date.strftime('%Y-%m-%d')} | {fvg_type} | Rango: {row['Bottom']:.2f} - {row['Top']:.2f} | Estado: {mitigated} (Mitigado en vela #{row['MitigatedIndex']})")
    print(f"Precio de Cierre Actual (MNQ): {df_d['close'].iloc[-1]:.2f}")
