#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import json
import subprocess
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def get_tick_multiplier(symbol):
    symbol = symbol.upper()
    if "NQ" in symbol or "MES" in symbol or "ES" in symbol:
        return 4.0, "ticks" # 0.25 tick size
    elif "GC" in symbol:
        return 10.0, "ticks" # 0.1 tick size
    elif "CL" in symbol:
        return 100.0, "ticks" # 0.01 tick size
    return 1.0, "pts"

def main():
    print("Iniciando cálculo automático de excursiones (MAE/MFE) desde TradingView...")
    
    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    mcp_cli_path = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
    journal_path = journal_dir / "journal.json"
    
    # 1. Obtener estado del gráfico para saber el símbolo activo
    state_result = subprocess.run(
        ["node", mcp_cli_path, "status"],
        capture_output=True,
        text=True
    )
    if state_result.returncode != 0:
        print(f"Error al conectar con TradingView: {state_result.stderr}", file=sys.stderr)
        return
        
    state_data = json.loads(state_result.stdout)
    if not state_data.get("success"):
        print(f"Error en estado de TradingView: {state_data.get('error')}", file=sys.stderr)
        return
        
    symbol = state_data.get("chart_symbol", "NQ1!")
    print(f"Gráfico activo detectado: {symbol}")

    # 2. Obtener dibujos manuales en tiempo real
    from utils import extract_cdp_drawings
    user_shapes = extract_cdp_drawings(mcp_cli_path)

    # Buscar herramientas de posición (Long/Short)
    positions = []
    for s in user_shapes:
        name = s.get("name", "")
        if "reward" in name.lower() or "position" in name.lower() or "ratio" in name.lower():
            positions.append(s)
            
    if not positions:
        print("No se encontró ninguna marcación de posición (Larga/Corta) activa en el gráfico.")
        return
        
    # Usar la posición más reciente (la última en el array)
    pos_shape = positions[-1]
    pts = pos_shape.get("points", [])
    if len(pts) < 2:
        print("La marcación de posición no tiene suficientes coordenadas.")
        return
        
    entry_price = pts[0].get("price")
    target_price = pts[1].get("price")
    stop_price = pts[2].get("price") if len(pts) > 2 else None
    
    if entry_price is None or target_price is None:
        print("No se pudieron extraer los niveles de precio del dibujo.")
        return
        
    direction = "Long"
    if "short" in pos_shape.get("name", "").lower():
        direction = "Short"
        
    # Cargar journal.json y validar coincidencia
    latest = None
    entries = []
    if journal_path.exists():
        try:
            entries = json.loads(journal_path.read_text(encoding="utf-8"))
            if entries:
                latest = entries[0]
            else:
                print("El archivo journal.json existe pero no tiene trades registrados.")
                return
        except Exception as e:
            print(f"Error al leer journal.json: {e}", file=sys.stderr)
            return
    else:
        print("No se encontró el archivo journal.json. Registra un trade en la UI primero.")
        return

    # Validar coincidencia de instrumento
    mkt_inst = latest.get("instrument", "").upper()
    if mkt_inst == "NQ" and "NQ" not in symbol.upper():
        print(f"⚠️ El último trade registrado es de NQ, pero el gráfico activo es {symbol}. Abortando.")
        return
    elif mkt_inst == "ES" and "ES" not in symbol.upper():
        print(f"⚠️ El último trade registrado es de ES, pero el gráfico activo es {symbol}. Abortando.")
        return

    # Validar coincidencia de dirección
    trade_dir = latest.get("direction", "")
    if trade_dir.lower() != direction.lower():
        print(f"⚠️ El último trade registrado es {trade_dir}, pero la posición dibujada en el gráfico es {direction}. Abortando.")
        return

    times = [pt.get("time") for pt in pts if pt.get("time") is not None]
    if not times:
        print("No se pudieron extraer las coordenadas de tiempo del dibujo.")
        return
        
    start_time = min(times)
    end_time = max(times)
    
    # Si los timestamps están en milisegundos, normalizar a segundos
    if start_time > 1e11:
        start_time /= 1000
    if end_time > 1e11:
        end_time /= 1000
        
    sl_str = f"{stop_price:.2f}" if stop_price else "N/A"
    print(f"Posición detectada: {direction} | Entrada: {entry_price:.2f} | TP: {target_price:.2f} | SL: {sl_str}")
    print(f"Rango de tiempo del trade: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))} a {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

    # 3. Descargar las velas del gráfico (500 velas para asegurar cobertura del trade)
    ohlcv_result = subprocess.run(
        ["node", mcp_cli_path, "ohlcv", "-n", "500"],
        capture_output=True,
        text=True
    )
    if ohlcv_result.returncode != 0:
        print(f"Error al descargar velas: {ohlcv_result.stderr}", file=sys.stderr)
        return
        
    ohlcv_data = json.loads(ohlcv_result.stdout)
    if not ohlcv_data.get("success"):
        print(f"Error en datos de velas: {ohlcv_data.get('error')}", file=sys.stderr)
        return
        
    bars = ohlcv_data["bars"]
    
    # Filtrar velas dentro del rango del trade (con 30 segundos de margen)
    matched_bars = []
    for bar in bars:
        bar_time = bar.get("time")
        if bar_time > 1e11:
            bar_time /= 1000
            
        if (start_time - 30) <= bar_time <= (end_time + 30):
            matched_bars.append(bar)
            
    if not matched_bars:
        print("No se encontraron velas en el historial que coincidan con el rango del trade. Asegúrate de estar en el timeframe correcto.")
        return
        
    print(f"Velas analizadas durante el trade: {len(matched_bars)}")
    
    lows = [b["low"] for b in matched_bars]
    highs = [b["high"] for b in matched_bars]
    
    min_low = min(lows)
    max_high = max(highs)
    
    # 4. Calcular MAE y MFE en precio
    if direction == "Long":
        mae_raw = entry_price - min_low
        mfe_raw = max_high - entry_price
    else:
        mae_raw = max_high - entry_price
        mfe_raw = entry_price - min_low
        
    # Impedir valores negativos por desfases pequeños de precisión
    mae_raw = max(0.0, mae_raw)
    mfe_raw = max(0.0, mfe_raw)
    
    # Convertir a ticks/puntos según el activo
    multiplier, unit = get_tick_multiplier(symbol)
    mae_val = mae_raw * multiplier
    mfe_val = mfe_raw * multiplier
    
    print(f"=== RESULTADOS MAE/MFE ===")
    print(f"MAE (Max Drawdown): {mae_val:.2f} {unit} | MFE (Max Run): {mfe_val:.2f} {unit}")

    # 5. Actualizar de forma automática el diario de trading (journal.json)
    latest["mae"] = round(float(mae_val), 1)
    latest["mfe"] = round(float(mfe_val), 1)
    
    try:
        # Escribir de vuelta a journal.json
        journal_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"¡Éxito! Se ha actualizado el último trade registrado en tu diario web con MAE/MFE ({latest.get('instrument')} {latest.get('direction')}).")
    except Exception as e:
        print(f"Error al actualizar journal.json: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
