#!/usr/bin/env python3
# encoding: utf-8
"""Script de automatización para guardar la información compacta de la Killzone.
Extrae velas de AMBOS mercados (MES y MNQ), dibujos de TradingView y ejecuciones
de NinjaTrader al cierre de sesión.

Correcciones aplicadas (Auditoría 2026-07-24):
- Captura dual de MES y MNQ (cambio de símbolo automático vía CDP).
- Zona horaria dinámica (soporta DST de Nueva York vs Guayaquil).
- Aumento de ventana de velas a -n 500 para cobertura garantizada.
- Protección contra sobreescritura destructiva de datos existentes.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Configurar encoding en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --- Constantes ---
SYMBOLS = ["CME_MINI:MES1!", "CME_MINI:MNQ1!"]
SYMBOL_KEYS = {"CME_MINI:MES1!": "MES", "CME_MINI:MNQ1!": "MNQ"}
MCP_CLI_PATH = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
NT8_URL = "http://localhost:7890/api/executions"
OHLCV_BAR_COUNT = "500"  # ~8.3 horas de cobertura en 1m

# Killzone en hora NYT (09:30 a 10:30 NYT)
KZ_START_NYT_H, KZ_START_NYT_M = 9, 30
KZ_END_NYT_H, KZ_END_NYT_M = 10, 30


def get_session_date():
    """Retorna la fecha de hoy en formato YYYY-MM-DD."""
    return time.strftime("%Y-%m-%d")


def get_killzone_timestamps(date_str):
    """Calcula los timestamps UTC de inicio y fin de la Killzone usando la zona
    horaria de Nueva York (soporta DST automáticamente).
    Retorna (start_ts, end_ts) en segundos UTC."""
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        # Fallback para Python < 3.9
        from backports.zoneinfo import ZoneInfo

    nyt = ZoneInfo("America/New_York")

    # Construir datetime naive y localizarlo a NYT
    start_naive = datetime.strptime(f"{date_str} {KZ_START_NYT_H:02d}:{KZ_START_NYT_M:02d}:00", "%Y-%m-%d %H:%M:%S")
    end_naive = datetime.strptime(f"{date_str} {KZ_END_NYT_H:02d}:{KZ_END_NYT_M:02d}:00", "%Y-%m-%d %H:%M:%S")

    start_nyt = start_naive.replace(tzinfo=nyt)
    end_nyt = end_naive.replace(tzinfo=nyt)

    # Convertir a timestamp UTC
    start_ts = start_nyt.timestamp()
    end_ts = end_nyt.timestamp()

    # Log para verificación
    local_start = datetime.fromtimestamp(start_ts).strftime("%H:%M:%S")
    local_end = datetime.fromtimestamp(end_ts).strftime("%H:%M:%S")
    print(f"   Killzone NYT: {KZ_START_NYT_H:02d}:{KZ_START_NYT_M:02d} - {KZ_END_NYT_H:02d}:{KZ_END_NYT_M:02d} | Local: {local_start} - {local_end}")

    return start_ts, end_ts


def run_cli_command(args, timeout=15):
    """Ejecuta un comando del CLI de TradingView y parsea el JSON resultante."""
    try:
        result = subprocess.run(
            ["node", MCP_CLI_PATH] + args,
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"  Error ejecutando CLI TradingView {args}: {e}", file=sys.stderr)
        return None


def switch_symbol(symbol):
    """Cambia el símbolo activo en TradingView vía CDP."""
    result = run_cli_command(["symbol", symbol], timeout=20)
    if result and result.get("success"):
        # Esperar a que el chart cargue completamente
        time.sleep(3)
        return True
    print(f"  ⚠️ No se pudo cambiar al símbolo {symbol}.", file=sys.stderr)
    return False


def fetch_ohlcv_bars(start_ts, end_ts):
    """Descarga las velas de 1m y filtra por el rango de la Killzone."""
    ohlcv_data = run_cli_command(["ohlcv", "-n", OHLCV_BAR_COUNT])
    if not ohlcv_data or not ohlcv_data.get("success"):
        return []

    bars = ohlcv_data.get("bars", [])
    filtered = []
    for bar in bars:
        bar_time = bar.get("time", 0)
        if bar_time > 1e11:  # Normalizar de milisegundos a segundos
            bar_time /= 1000
        if start_ts <= bar_time <= end_ts:
            filtered.append({
                "time": bar.get("time"),
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "close": bar.get("close"),
                "volume": bar.get("volume")
            })
    return filtered


def fetch_drawings():
    """Extrae los dibujos manuales del gráfico activo de TradingView vía CDP."""
    from utils import extract_cdp_drawings
    return extract_cdp_drawings(MCP_CLI_PATH)


def fetch_executions(date_str):
    """Consulta la API de ejecuciones de NinjaTrader 8 y filtra por fecha."""
    import urllib.request
    try:
        req = urllib.request.Request(NT8_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            raw = data.get("value", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            return [exe for exe in raw if exe.get("time", "").startswith(date_str)]
    except Exception as e:
        print(f"  NinjaTrader 8 no disponible: {e}", file=sys.stderr)
        return []


def safe_merge(existing, new_data, key):
    """Preserva datos existentes si la nueva consulta retorna vacío (protección anti-sobreescritura)."""
    if not new_data and existing.get(key):
        print(f"  🛡️ Preservando datos existentes para '{key}' (nueva consulta retornó vacío).")
        return existing[key]
    return new_data


def main():
    print("=" * 60)
    print("🚀 GRABADOR DE DATOS DE SESIÓN DE LA KILLZONE (Dual Market)")
    print("=" * 60)

    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    output_dir = journal_dir / "historical_data"
    output_dir.mkdir(exist_ok=True)

    date_str = get_session_date()
    output_file = output_dir / f"{date_str}.json"

    # Cargar datos existentes si el archivo ya existe (protección anti-sobreescritura)
    existing_data = {}
    if output_file.exists():
        try:
            existing_data = json.loads(output_file.read_text(encoding="utf-8"))
            print(f"📂 Archivo existente detectado: {output_file.name}. Se fusionarán datos.")
        except Exception:
            existing_data = {}

    # 1. Calcular timestamps de la Killzone con zona horaria dinámica
    print("\n1. Calculando rango de la Killzone (zona horaria dinámica)...")
    start_ts, end_ts = get_killzone_timestamps(date_str)

    # 2. Capturar datos de AMBOS mercados (MES y MNQ)
    print("\n2. Capturando datos duales (MES y MNQ) desde TradingView...")
    symbols_data = existing_data.get("symbols", {})

    for symbol_full, symbol_key in SYMBOL_KEYS.items():
        print(f"\n  --- Procesando {symbol_key} ({symbol_full}) ---")

        # Cambiar símbolo en TradingView
        if not switch_symbol(symbol_full):
            symbols_data[symbol_key] = safe_merge(
                symbols_data, {}, symbol_key
            ) if symbol_key in symbols_data else {"bars_1m": [], "drawings": []}
            continue

        # Cambiar a temporalidad de 1m
        run_cli_command(["timeframe", "1"], timeout=10)
        time.sleep(1)

        # Descargar velas de 1m filtradas por la Killzone
        bars = fetch_ohlcv_bars(start_ts, end_ts)
        print(f"  -> Velas de 1m en la Killzone: {len(bars)}")

        # Extraer dibujos manuales del gráfico activo
        drawings = fetch_drawings()
        print(f"  -> Marcaciones detectadas: {len(drawings)}")

        # Fusionar con datos existentes (protección)
        existing_symbol = symbols_data.get(symbol_key, {})
        symbols_data[symbol_key] = {
            "bars_1m": safe_merge(existing_symbol, bars, "bars_1m"),
            "drawings": safe_merge(existing_symbol, drawings, "drawings")
        }

    # 3. Consultar ejecuciones de NinjaTrader 8
    print("\n3. Extrayendo ejecuciones reales de la sesión (NinjaTrader 8)...")
    executions = fetch_executions(date_str)
    executions = safe_merge(existing_data, executions, "executions")
    print(f"  -> Ejecuciones registradas hoy: {len(executions)}")

    # 4. Guardar base de datos consolidada
    session_data = {
        "date": date_str,
        "killzone_range_nyt": f"{KZ_START_NYT_H:02d}:{KZ_START_NYT_M:02d}-{KZ_END_NYT_H:02d}:{KZ_END_NYT_M:02d}",
        "resolution": "1",
        "symbols": symbols_data,
        "executions": executions
    }

    try:
        output_file.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ DATOS DE SESIÓN GUARDADOS: {output_file.resolve()}")
        # Resumen de tamaño
        size_kb = output_file.stat().st_size / 1024
        print(f"   Tamaño del archivo: {size_kb:.1f} KB")
    except Exception as e:
        print(f"❌ Error al guardar archivo JSON de sesión: {e}", file=sys.stderr)

    print("=" * 60)


if __name__ == "__main__":
    main()
