import os
os.environ["SMC_CREDIT"] = "0"
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
import json
import pandas as pd
import numpy as np
import yfinance as yf
from smartmoneyconcepts import smc

def fetch_data(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {symbol} {interval}: {e}", file=sys.stderr)
        return None

def analyze_tf_smc(df, swing_len=5):
    if df is None or len(df) < 15:
        return {}
    swings = smc.swing_highs_lows(df, swing_length=swing_len)
    obs = smc.ob(df, swings)
    fvgs = smc.fvg(df)
    bos_choch = smc.bos_choch(df, swings)
    
    last_price = float(df["close"].iloc[-1])
    
    active_obs = obs[obs["OB"].notna() & (obs["OB"] != 0) & ((obs["MitigatedIndex"] == 0) | obs["MitigatedIndex"].isna())]
    active_fvgs = fvgs[fvgs["FVG"].notna() & (fvgs["FVG"] != 0) & ((fvgs["MitigatedIndex"] == 0) | fvgs["MitigatedIndex"].isna())]
    
    recent_bos = bos_choch.dropna(subset=["BOS", "CHOCH"], how="all").tail(2)
    bias = "Neutral"
    if len(recent_bos) > 0:
        last_struct = recent_bos.iloc[-1]
        if not pd.isna(last_struct["BOS"]):
            bias = "Bullish 🟢" if last_struct["BOS"] == 1 else "Bearish 🔴"
        elif not pd.isna(last_struct["CHOCH"]):
            bias = "Bullish 🟢" if last_struct["CHOCH"] == 1 else "Bearish 🔴"
            
    # Calculate premium vs discount based on last significant swing range
    swing_highs = swings[swings["HighLow"] == 1]
    swing_lows = swings[swings["HighLow"] == -1]
    
    range_state = "Unknown"
    if len(swing_highs) > 0 and len(swing_lows) > 0:
        sh = float(swing_highs["Level"].iloc[-1])
        sl = float(swing_lows["Level"].iloc[-1])
        mid = (sh + sl) / 2
        if sh > sl:
            range_state = "Premium (Ventas) 🔴" if last_price > mid else "Discount (Compras) 🟢"
        else:
            range_state = "Discount (Compras) 🟢" if last_price > mid else "Premium (Ventas) 🔴"
            
    formatted_obs = []
    for idx, row in active_obs.tail(3).iterrows():
        formatted_obs.append({
            "type": "Demand" if row["OB"] == 1 else "Supply",
            "bottom": float(row["Bottom"]),
            "top": float(row["Top"]),
            "volume": float(row["OBVolume"]) if "OBVolume" in row else 0
        })
        
    formatted_fvgs = []
    for idx, row in active_fvgs.tail(3).iterrows():
        # Get candles for profile
        c_idx = int(idx)
        profile = "Unknown"
        if c_idx >= 2 and c_idx < len(df):
            c1 = "G" if df["close"].iloc[c_idx-2] >= df["open"].iloc[c_idx-2] else "R"
            c2 = "G" if df["close"].iloc[c_idx-1] >= df["open"].iloc[c_idx-1] else "R"
            c3 = "G" if df["close"].iloc[c_idx] >= df["open"].iloc[c_idx] else "R"
            profile = f"{c1}-{c2}-{c3}"
            
        formatted_fvgs.append({
            "type": "Bullish" if row["FVG"] == 1 else "Bearish",
            "bottom": float(row["Bottom"]),
            "top": float(row["Top"]),
            "profile": profile
        })
        
    return {
        "bias": bias,
        "range_state": range_state,
        "obs": formatted_obs,
        "fvgs": formatted_fvgs,
        "last_price": last_price
    }

def main():
    print("Iniciando análisis Top-Down Multitemporalidad Completo (1m a 4h)...")
    
    # 1. Fetch 1h and resample to 4h
    df_1h = fetch_data("NQ=F", "1h", "60d")
    df_4h = None
    if df_1h is not None:
        df_4h = df_1h.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
    # 2. Fetch other timeframes
    df_30m = fetch_data("NQ=F", "30m", "10d")
    df_15m = fetch_data("NQ=F", "15m", "5d")
    df_5m = fetch_data("NQ=F", "5m", "5d")
    df_4m = fetch_data("NQ=F", "2m", "5d") # Using 2m as proxy or resample, but wait we can fetch 2m and 5m
    df_3m = fetch_data("NQ=F", "2m", "5d") # yfinance doesn't support 3m and 4m directly, we will use 2m and 5m, or resample 1m!
    df_2m = fetch_data("NQ=F", "2m", "5d")
    df_1m = fetch_data("NQ=F", "1m", "2d")
    
    results = {}
    
    # Analyze macro
    results["4H"] = analyze_tf_smc(df_4h, swing_len=5)
    results["1H"] = analyze_tf_smc(df_1h, swing_len=5)
    
    # Analyze medium
    results["30m"] = analyze_tf_smc(df_30m, swing_len=5)
    results["15m"] = analyze_tf_smc(df_15m, swing_len=5)
    
    # Analyze micro
    results["5m"] = analyze_tf_smc(df_5m, swing_len=5)
    results["2m"] = analyze_tf_smc(df_2m, swing_len=5)
    results["1m"] = analyze_tf_smc(df_1m, swing_len=5)
    
    # Format and output beautifully
    print("\n" + "="*60)
    print("=== REPORTE MULTI-TEMPORALIDAD COMPLETO (SMC/ICT) ===")
    print("="*60)
    
    for tf in ["4H", "1H", "30m", "15m", "5m", "2m", "1m"]:
        res = results.get(tf, {})
        if not res:
            print(f"\n[Temporalidad {tf}] - No se pudieron descargar o calcular datos.")
            continue
        print(f"\n⚡ [{tf}] | Precio: {res['last_price']:.2f} | Bias: {res['bias']} | Zona: {res['range_state']}")
        
        if res.get("obs"):
            print("   Order Blocks Activos:")
            for ob in res["obs"]:
                print(f"     * OB {ob['type']} en {ob['bottom']:.2f} - {ob['top']:.2f}")
        if res.get("fvgs"):
            print("   FVGs Activos:")
            for fvg in res["fvgs"]:
                print(f"     * FVG {fvg['type']} en {fvg['bottom']:.2f} - {fvg['top']:.2f} | Perfil: {fvg['profile']}")
                
    print("\n" + "="*60)
    print("=========================================================")

if __name__ == "__main__":
    main()
