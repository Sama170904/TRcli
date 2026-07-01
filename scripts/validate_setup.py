import os
import sys
import json
import urllib.request
import urllib.parse

def local_request(endpoint):
    url = f"http://localhost:7890{endpoint}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None

def check_fvg(bars):
    """
    Analiza si hay un FVG o iFVG reciente (últimas 3-4 velas).
    Retorna (fvg_active, fvg_type, is_inverted, profile_desc)
    """
    if len(bars) < 4:
        return False, None, False, "Datos insuficientes"
    
    # Un FVG alcista se forma cuando High[i-2] < Low[i] (dejando un gap)
    # Un FVG bajista se forma cuando Low[i-2] > High[i] (dejando un gap)
    
    # Velas indexadas cronológicamente (bars[-1] es la vela actual, bars[-2] la anterior, etc.)
    low_3 = bars[-1]["low"]
    high_1 = bars[-3]["high"]
    
    # Perfil de color
    def get_color(b):
        return "G" if b["close"] >= b["open"] else "R"
    profile = f"{get_color(bars[-3])}-{get_color(bars[-2])}-{get_color(bars[-1])}"
    
    # FVG Alcista (Bullish) normal
    if low_3 > high_1:
        return True, "Bullish", False, f"FVG Bullish activo ({high_1:.2f} - {low_3:.2f}) | Perfil: {profile}"
    
    # FVG Bajista (Bearish) normal
    high_3 = bars[-1]["high"]
    low_1 = bars[-3]["low"]
    if high_3 < low_1:
        return True, "Bearish", False, f"FVG Bearish activo ({high_3:.2f} - {low_1:.2f}) | Perfil: {profile}"
        
    # Buscar Inversiones (iFVG) en la vela actual bars[-1]
    # Si había un FVG bajista entre -4 y -2 (Low[-4] > High[-2])
    # y la vela actual bars[-1] cerró por ENCIMA del límite superior (Low[-4])
    if len(bars) >= 4:
        low_4 = bars[-4]["low"]
        high_2 = bars[-2]["high"]
        if low_4 > high_2:
            if bars[-1]["close"] > low_4:
                return True, "Bullish", True, f"iFVG Bullish ACTIVO 🟢 (Invertido en {low_4:.2f}) | Perfil: {profile}"
                
        # Si había un FVG alcista entre -4 y -2 (High[-4] < Low[-2])
        # y la vela actual bars[-1] cerró por DEBAJO del límite inferior (High[-4])
        high_4 = bars[-4]["high"]
        low_2 = bars[-2]["low"]
        if high_4 < low_2:
            if bars[-1]["close"] < high_4:
                return True, "Bearish", True, f"iFVG Bearish ACTIVO 🔴 (Invertido en {high_4:.2f}) | Perfil: {profile}"

    return False, None, False, "Sin gaps recientes"

def detect_absorption(bars, delta_val):
    """
    Detecta absorción de volumen en base a volumen, rango físico y mechas.
    """
    if len(bars) < 3:
        return False, "Datos insuficientes"
        
    last_bar = bars[-1]
    bar_range = last_bar["high"] - last_bar["low"]
    
    # Calcular volumen promedio
    volumes = [b["volume"] for b in bars[:-1]]
    avg_vol = sum(volumes) / len(volumes) if volumes else 1.0
    
    # Calcular rango promedio
    ranges = [b["high"] - b["low"] for b in bars[:-1]]
    avg_range = sum(ranges) / len(ranges) if ranges else 1.0
    
    is_high_volume = last_bar["volume"] > (avg_vol * 1.3)
    is_narrow_range = bar_range < (avg_range * 0.9)
    
    # Absorción por volumen alto en rango estrecho (esfuerzo sin resultado)
    if is_high_volume and is_narrow_range:
        delta_str = f"Absorción por rango estrecho con volumen alto ({last_bar['volume']} vs prom {avg_vol:.0f})"
        if delta_val is not None:
            delta_str += f" | Delta Actual: {delta_val}"
        return True, delta_str
        
    # Absorción por mecha larga en volumen alto
    if bar_range > 0:
        upper_wick = last_bar["high"] - max(last_bar["open"], last_bar["close"])
        lower_wick = min(last_bar["open"], last_bar["close"]) - last_bar["low"]
        
        if lower_wick > (bar_range * 0.5) and is_high_volume:
            return True, f"Absorción ALCISTA en mecha inferior con volumen ({last_bar['volume']})"
        if upper_wick > (bar_range * 0.5) and is_high_volume:
            return True, f"Absorción BAJISTA en mecha superior con volumen ({last_bar['volume']})"

    return False, "Sin volumen de parada o absorción clara"

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
        
    print("==================================================")
    print("🔍 VALIDACIÓN VELOZ DE SETUP EN VIVO - NINJATRADER")
    print("==================================================")
    
    # 1. Consultar estado del gráfico activo
    charts = local_request("/api/chart/state")
    if not charts:
        print("❌ Error: No se pudo conectar a NinjaTrader o no hay gráficos abiertos.")
        sys.exit(1)
        
    # Obtener el primer símbolo activo
    active_chart = charts[0]
    symbol = active_chart.get("instrument")
    print(f"Símbolo detectado en NinjaTrader: {symbol}")
    
    # Leer el delta acumulado en vivo si el indicador existe
    delta_indicator_name = "Order Flow Cumulative Delta"
    encoded_sym = urllib.parse.quote(symbol)
    encoded_ind = urllib.parse.quote(delta_indicator_name)
    delta_response = local_request(f"/api/indicator/{encoded_sym}/{encoded_ind}")
    current_delta = None
    if delta_response and "value" in delta_response:
        current_delta = delta_response["value"]
    
    timeframes = [1, 2, 3, 4, 5]
    setup_found = False
    
    print("\nCalculando confluencias en marcos temporales bajos (LTF)...")
    print("-" * 50)
    
    verdicts = []
    
    for tf in timeframes:
        # Traer últimas 10 velas para ese timeframe
        bars_resp = local_request(f"/api/bars/{encoded_sym}?interval={tf}&bars=10")
        if not bars_resp or (isinstance(bars_resp, dict) and "success" in bars_resp and bars_resp["success"] is False):
            print(f"[{tf}m] ⚠️ No se detectó un gráfico abierto de {tf}m en NinjaTrader.")
            continue
            
        bars = bars_resp
        if len(bars) < 4:
            print(f"[{tf}m] ⚠️ Datos insuficientes en el gráfico.")
            continue
            
        # Validar FVG / iFVG
        has_fvg, fvg_type, is_inverted, fvg_desc = check_fvg(bars)
        
        # Validar Absorción
        has_abs, abs_desc = detect_absorption(bars, current_delta)
        
        status_icons = []
        if has_fvg:
            if is_inverted:
                status_icons.append("iFVG 🟢" if fvg_type == "Bullish" else "iFVG 🔴")
            else:
                status_icons.append(f"FVG {fvg_type} 🟡")
        if has_abs:
            status_icons.append("ABS 🌊")
            
        status_str = " | ".join(status_icons) if status_icons else "Sin confluencia"
        print(f"[{tf}m] {status_str}")
        print(f"      ↳ Gaps: {fvg_desc}")
        print(f"      ↳ Flujo: {abs_desc}")
        
        if is_inverted or has_abs:
            setup_found = True
            if is_inverted:
                verdicts.append(f"iFVG {fvg_type} en {tf}m (Gatillo de {'Compra' if fvg_type=='Bullish' else 'Venta'})")
            if has_abs:
                verdicts.append(f"Absorción de volumen en {tf}m")
                
    print("-" * 50)
    if setup_found:
        print("\n👉 VERDICTO DEL MENTOR IA:")
        print("  🟢 SETUP OPERATIVO DETECTADO:")
        for v in verdicts:
            print(f"  * {v}")
        print("\n  ⚠️ Recuerda validar frente a las Zonas de Peligro (Premium/Discount HTF) y noticias antes de hacer clic.")
    else:
        print("\n👉 VERDICTO DEL MENTOR IA:")
        print("  ❌ NO SE DETECTAN GATILLOS CLAROS EN ESTE SEGUNDO.")
        print("  * Espera un desplazamiento que invierta un FVG (iFVG) o una absorción de volumen institucional clara.")
    print("==================================================")

if __name__ == "__main__":
    main()
