import os
os.environ["SMC_CREDIT"] = "0"
import yfinance as yf
import pandas as pd
from smartmoneyconcepts import smc

def analyze(symbol, name):
    print(f"\n=== {name} ({symbol}) ===")
    # Daily
    df_d = yf.download(symbol, period="3mo", interval="1d", progress=False)
    if not df_d.empty:
        df_d.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_d.columns]
        fvgs_d = smc.fvg(df_d)
        active_fvgs_d = fvgs_d[fvgs_d["FVG"].notna() & (fvgs_d["FVG"] != 0) & ((fvgs_d["MitigatedIndex"] == 0) | fvgs_d["MitigatedIndex"].isna())]
        print("Daily Active FVGs:")
        for idx, row in active_fvgs_d.tail(5).iterrows():
            fvg_type = "Bullish" if row["FVG"] == 1 else "Bearish"
            date_str = df_d.index[idx].strftime('%Y-%m-%d') if idx < len(df_d) else str(idx)
            print(f"  - {fvg_type}: {row['Bottom']:.2f} - {row['Top']:.2f} (Vela {date_str})")
        print(f"Daily Close: {df_d['close'].iloc[-1]:.2f}")
    
    # 4H
    df_1h = yf.download(symbol, period="1mo", interval="1h", progress=False)
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
        active_fvgs_4h = fvgs_4h[fvgs_4h["FVG"].notna() & (fvgs_4h["FVG"] != 0) & ((fvgs_4h["MitigatedIndex"] == 0) | fvgs_4h["MitigatedIndex"].isna())]
        print("4H Active FVGs:")
        for idx, row in active_fvgs_4h.tail(5).iterrows():
            fvg_type = "Bullish" if row["FVG"] == 1 else "Bearish"
            date_str = df_4h.index[idx].strftime('%Y-%m-%d %H:%M') if idx < len(df_4h) else str(idx)
            print(f"  - {fvg_type}: {row['Bottom']:.2f} - {row['Top']:.2f} (Vela {date_str})")

analyze("MNQ=F", "Nasdaq Micros")
analyze("MES=F", "S&P 500 Micros")
