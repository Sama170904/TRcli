import subprocess
import json
import time
import os
import sys

mcp_cli = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
python_exec = sys.executable
analyze_smc_path = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\scripts\analyze_smc.py"

symbols = {
    "MES": "CME_MINI:MES1!",
    "MNQ": "CME_MINI:MNQ1!"
}
timeframes = ["1", "2", "3", "4", "5", "15", "30", "1h", "4h"]

results = {}

for sym_name, sym_code in symbols.items():
    print(f"=== Procesando {sym_name} ({sym_code}) ===")
    
    # 1. Cambiar simbolo en TradingView
    subprocess.run(["node", mcp_cli, "symbol", sym_code], capture_output=True, text=True)
    time.sleep(3.0)
    
    # 2. Correr el escaner premarket para este simbolo
    print(f"Ejecutando escaner premarket para {sym_name}...")
    subprocess.run([python_exec, analyze_smc_path], cwd=os.path.dirname(analyze_smc_path), capture_output=True, text=True)
    
    results[sym_name] = {}
    
    # 3. Iterar por cada temporalidad
    for tf in timeframes:
        print(f"  Temporalidad {tf}...")
        
        # Cambiar temporalidad
        subprocess.run(["node", mcp_cli, "timeframe", tf], capture_output=True, text=True)
        time.sleep(3.0)
        
        # Tomar captura
        screenshot_filename = f"{sym_name}_{tf}"
        subprocess.run(["node", mcp_cli, "screenshot", "-o", screenshot_filename], capture_output=True, text=True)
        
        # Obtener velas
        ohlcv_res = subprocess.run(["node", mcp_cli, "ohlcv", "-n", "5"], capture_output=True, text=True)
        
        bars = []
        if ohlcv_res.returncode == 0:
            try:
                data = json.loads(ohlcv_res.stdout)
                if data.get("success"):
                    bars = data.get("bars", [])
            except Exception as e:
                print(f"    Error parseando velas en {sym_name} {tf}: {e}")
        
        results[sym_name][tf] = {
            "bars": bars,
            "screenshot": f"{screenshot_filename}.png"
        }

# Guardar resultados en JSON
output_path = r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\scratch\ohlcv_scan_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Escaneo completo. Resultados guardados en: {output_path}")
