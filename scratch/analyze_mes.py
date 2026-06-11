import sys
import os
import pandas as pd
import json

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from analyze_smc import fetch_htf_data, analyze_tf_structure

def main():
    yf_symbol = "MES=F"
    df_1m = fetch_htf_data(yf_symbol, interval="1m", period="2d", count=500)
    df_2m = fetch_htf_data(yf_symbol, interval="2m", period="5d", count=200)
    df_5m = fetch_htf_data(yf_symbol, interval="5m", period="5d", count=200)
    df_15m = fetch_htf_data(yf_symbol, interval="15m", period="5d", count=200)
    df_30m = fetch_htf_data(yf_symbol, interval="30m", period="10d", count=200)
    df_1h = fetch_htf_data(yf_symbol, interval="1h", period="30d", count=200)
    
    df_3m = None
    df_4m = None
    df_4h = None
    
    if df_1m is not None:
        df_3m = df_1m.resample('3min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().tail(200)
        df_4m = df_1m.resample('4min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().tail(200)
        
    if df_1h is not None:
        df_4h = df_1h.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().tail(200)
        
    all_tf_analysis = {
        "4H": analyze_tf_structure(df_4h, swing_len=5),
        "1H": analyze_tf_structure(df_1h, swing_len=5),
        "30m": analyze_tf_structure(df_30m, swing_len=5),
        "15m": analyze_tf_structure(df_15m, swing_len=5),
        "5m": analyze_tf_structure(df_5m, swing_len=5),
        "4m": analyze_tf_structure(df_4m, swing_len=5),
        "3m": analyze_tf_structure(df_3m, swing_len=5),
        "2m": analyze_tf_structure(df_2m, swing_len=5),
        "1m": analyze_tf_structure(df_1m, swing_len=5),
    }
    
    print(json.dumps(all_tf_analysis, indent=2))

if __name__ == "__main__":
    main()
