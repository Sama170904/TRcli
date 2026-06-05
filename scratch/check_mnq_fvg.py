import yfinance as yf
import pandas as pd

print("Descargando datos de 5m de MNQ=F desde Yahoo Finance...")
df = yf.download("MNQ=F", period="1d", interval="5m", progress=False)

if df.empty:
    print("No se encontraron datos.")
    exit(1)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
else:
    df.columns = [c.lower() for c in df.columns]

print(df.tail(8))

# Let's check for a bearish FVG in the last few candles
# Bearish FVG condition at index i: High(i) < Low(i-2) with a bearish displacement candle at i-1
# Let's inspect the last 5 indices
for i in range(len(df) - 5, len(df)):
    if i < 2: continue
    high_i = float(df['high'].iloc[i])
    low_i_minus_2 = float(df['low'].iloc[i-2])
    close_i_minus_1 = float(df['close'].iloc[i-1])
    open_i_minus_1 = float(df['open'].iloc[i-1])
    
    # Check if there is an imbalance
    if high_i < low_i_minus_2:
        # FVG Bearish
        gap_size = low_i_minus_2 - high_i
        print(f"\n[DETECTADO] FVG Bearish en índice {i} (Tiempo: {df.index[i]}):")
        print(f"  Rango FVG: {high_i:.2f} - {low_i_minus_2:.2f} (Tamaño: {gap_size:.2f})")
        print(f"  Vela en medio: Open={open_i_minus_1:.2f}, Close={close_i_minus_1:.2f}")
