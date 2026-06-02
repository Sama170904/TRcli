#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import json
import subprocess
import time
from pathlib import Path

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
    js_get_drawings = r"""(function(){
    try {
        var api = window.TradingViewApi._activeChartWidgetWV.value();
        var all = api.getAllShapes();
        var drawings = [];
        for (var i = 0; i < all.length; i++) {
            var s = all[i];
            var shape = api.getShapeById(s.id);
            if (shape) {
                var pts = null;
                try { pts = shape.getPoints(); } catch(e) {}
                if (!pts) { try { pts = shape.points(); } catch(e) {} }
                var props = null;
                try { props = shape.getProperties(); } catch(e) {}
                if (!props) { try { props = shape.properties(); } catch(e) {} }
                drawings.push({
                    id: s.id,
                    name: s.name,
                    points: pts,
                    properties: props
                });
            }
        }
        return { success: true, drawings: drawings };
    } catch(e) {
        return { success: false, error: e.message };
    }
    })()"""

    drawings_eval = subprocess.run(
        ["node", mcp_cli_path, "ui", "eval", js_get_drawings],
        capture_output=True,
        text=True
    )
    
    user_shapes = []
    if drawings_eval.returncode == 0:
        try:
            draw_data = json.loads(drawings_eval.stdout)
            if draw_data.get("success"):
                if "result" in draw_data and isinstance(draw_data["result"], dict):
                    user_shapes = draw_data["result"].get("drawings", [])
                else:
                    user_shapes = draw_data.get("drawings", [])
        except Exception as e:
            print(f"Error parseando dibujos manuales: {e}", file=sys.stderr)
            return

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
    if target_price < entry_price:
        direction = "Short"
        
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
    if journal_path.exists():
        try:
            entries = json.loads(journal_path.read_text(encoding="utf-8"))
            if entries:
                # Actualizar el trade más reciente (el primero en la lista)
                latest = entries[0]
                latest["mae"] = f"{mae_val:.1f}"
                latest["mfe"] = f"{mfe_val:.1f}"
                
                # Escribir de vuelta a journal.json
                journal_path.write_text(
                    json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"¡Éxito! Se ha actualizado el último trade registrado en tu diario web con MAE/MFE ({latest.get('instrument')} {latest.get('direction')}).")
            else:
                print("El archivo journal.json existe pero no tiene trades registrados.")
        except Exception as e:
            print(f"Error al actualizar journal.json: {e}", file=sys.stderr)
    else:
        print("No se encontró el archivo journal.json. Registra un trade en la UI primero.")

if __name__ == "__main__":
    main()
