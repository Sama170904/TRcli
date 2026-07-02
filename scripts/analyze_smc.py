import os
os.environ["SMC_CREDIT"] = "0"
import sys
import json
import subprocess
import time
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from smartmoneyconcepts import smc
import yfinance as yf
import urllib.request
import urllib.parse

def get_candle_color(open_p, close_p):
    return "G" if close_p >= open_p else "R"

def analyze_fvg_profile(df, idx, fvg_type):
    """
    Analiza la anatomía de 3 velas del FVG según las reglas del manual del usuario:
    - Red-Green-Red (Bearish FVG) / Green-Red-Green (Bullish FVG) -> Easy to invert
    - Red-Green-Green / Green-Green-Red -> Medium difficulty
    - Green-Green-Green / Red-Red-Red -> Strong displacement (highly respected)
    """
    if idx < 2:
        return "Desconocido", "Extra Confirmación"
        
    c1 = get_candle_color(df["open"].iloc[idx-2], df["close"].iloc[idx-2])
    c2 = get_candle_color(df["open"].iloc[idx-1], df["close"].iloc[idx-1])
    c3 = get_candle_color(df["open"].iloc[idx], df["close"].iloc[idx])
    
    profile = f"{c1}-{c2}-{c3}"
    
    if fvg_type == 1:  # Bullish FVG
        if profile == "G-R-G":
            return profile, "Fácil de Invertir (iFVG de Alta Probabilidad) 🔴"
        elif profile == "G-G-R":
            return profile, "Dificultad Media (Requiere extra confirmación) 🟡"
        elif profile == "G-G-G":
            return profile, "Fuerte Desplazamiento Alcista (Gran probabilidad de ser Respetado) 🟢"
        else:
            return profile, "Moderado (Extra Confirmación) 🟡"
    else:  # Bearish FVG
        if profile == "R-G-R":
            return profile, "Fácil de Invertir (iFVG de Alta Probabilidad) 🟢"
        elif profile == "R-G-G":
            return profile, "Dificultad Media (Requiere extra confirmación) 🟡"
        elif profile == "R-R-R":
            return profile, "Fuerte Desplazamiento Bajista (Gran probabilidad de ser Respetado) 🔴"
        else:
            return profile, "Moderado (Extra Confirmación) 🟡"

def fetch_htf_data(symbol_yf, interval, period, count=100):
    """Descarga de forma silenciosa datos históricos para análisis multi-temporalidad"""
    try:
        df = yf.download(symbol_yf, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        # Convertir columnas a minúsculas, aplanando MultiIndex si es necesario
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        # Asegurar tipos float
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df.tail(count)
    except Exception as e:
        print(f"Advertencia al descargar temporalidad HTF ({interval}) para {symbol_yf}: {e}", file=sys.stderr)
        return None

def analyze_tf_structure(df, swing_len=5):
    """Analiza la estructura SMC para una temporalidad específica"""
    if df is None or len(df) < 15:
        return {"bias": "Neutral", "range_state": "Desconocido", "obs": [], "fvgs": [], "last_price": 0.0}
    try:
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
                
        # Premium vs Discount
        swing_highs = swings[swings["HighLow"] == 1]
        swing_lows = swings[swings["HighLow"] == -1]
        
        range_state = "Desconocido"
        if len(swing_highs) > 0 and len(swing_lows) > 0:
            sh = float(swing_highs["Level"].iloc[-1])
            sl = float(swing_lows["Level"].iloc[-1])
            mid = (sh + sl) / 2
            if sh > sl:
                range_state = "Premium (Ventas) 🔴" if last_price > mid else "Discount (Compras) 🟢"
            else:
                range_state = "Discount (Compras) 🟢" if last_price > mid else "Premium (Ventas) 🔴"
                
        formatted_obs = []
        for idx, row in active_obs.tail(2).iterrows():
            formatted_obs.append({
                "type": "Demand" if row["OB"] == 1 else "Supply",
                "bottom": float(row["Bottom"]),
                "top": float(row["Top"])
            })
            
        formatted_fvgs = []
        for idx, row in active_fvgs.tail(2).iterrows():
            formatted_fvgs.append({
                "type": "Bullish" if row["FVG"] == 1 else "Bearish",
                "bottom": float(row["Bottom"]),
                "top": float(row["Top"])
            })
            
        return {
            "bias": bias,
            "range_state": range_state,
            "obs": formatted_obs,
            "fvgs": formatted_fvgs,
            "last_price": last_price
        }
    except Exception as e:
        print(f"Error analizando estructura: {e}", file=sys.stderr)
        return {"bias": "Neutral", "range_state": "Error", "obs": [], "fvgs": [], "last_price": 0.0}

def check_smt_divergence():
    """Calcula la divergencia SMT entre Nasdaq (MNQ) y S&P 500 (MES) en LTF 2m"""
    try:
        df_nq = yf.download("MNQ=F", period="5d", interval="2m", progress=False).tail(40)
        df_es = yf.download("MES=F", period="5d", interval="2m", progress=False).tail(40)
        
        if df_nq.empty or df_es.empty:
            return None
            
        if isinstance(df_nq.columns, pd.MultiIndex):
            df_nq.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_nq.columns]
        else:
            df_nq.columns = [c.lower() for c in df_nq.columns]
            
        if isinstance(df_es.columns, pd.MultiIndex):
            df_es.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df_es.columns]
        else:
            df_es.columns = [c.lower() for c in df_es.columns]
        
        swings_nq = smc.swing_highs_lows(df_nq, swing_length=3)
        swings_es = smc.swing_highs_lows(df_es, swing_length=3)
        
        lows_nq = swings_nq[swings_nq["HighLow"] == -1].tail(2)
        lows_es = swings_es[swings_es["HighLow"] == -1].tail(2)
        
        highs_nq = swings_nq[swings_nq["HighLow"] == 1].tail(2)
        highs_es = swings_es[swings_es["HighLow"] == 1].tail(2)
        
        if len(lows_nq) >= 2 and len(lows_es) >= 2:
            nq_l1, nq_l2 = lows_nq["Level"].iloc[-2], lows_nq["Level"].iloc[-1]
            es_l1, es_l2 = lows_es["Level"].iloc[-2], lows_es["Level"].iloc[-1]
            if nq_l2 > nq_l1 and es_l2 < es_l1:
                return "SMT ALCISTA DETECTADO 🟢 (Nasdaq sostiene mínimos más altos mientras S&P barre a mínimos más bajos. ¡Acumulación institucional!)"
                
        if len(highs_nq) >= 2 and len(highs_es) >= 2:
            nq_h1, nq_h2 = highs_nq["Level"].iloc[-2], highs_nq["Level"].iloc[-1]
            es_h1, es_h2 = highs_es["Level"].iloc[-2], highs_es["Level"].iloc[-1]
            if nq_h2 < nq_h1 and es_h2 > es_h1:
                return "SMT BAJISTA DETECTADO 🔴 (Nasdaq hace máximos más bajos mientras S&P expande a máximos más altos. ¡Distribución institucional!)"
                
        return None
    except Exception as e:
        return f"Advertencia SMT: No se pudo conectar a los servidores de datos de S&P 500: {e}"

def get_ninjatrader_orderflow():
    """Consulta el servidor de NinjaTrader para obtener confluencias de Order Flow"""
    try:
        url_state = "http://localhost:7890/api/chart/state"
        req = urllib.request.Request(url_state, method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                charts = json.loads(response.read().decode("utf-8"))
                orderflow_data = []
                for chart in charts:
                    symbol = chart.get("instrument")
                    timeframe = chart.get("timeframe")
                    indicators = chart.get("indicators", [])
                    
                    # Filtrar indicadores relacionados con flujo de órdenes
                    of_indicators = [ind for ind in indicators if any(keyword in ind.lower() for keyword in ["order flow", "cumulative delta", "volumetric", "delta", "volumen", "volume"])]
                    
                    indicator_values = {}
                    for ind in of_indicators:
                        encoded_symbol = urllib.parse.quote(symbol)
                        encoded_ind = urllib.parse.quote(ind)
                        url_val = f"http://localhost:7890/api/indicator/{encoded_symbol}/{encoded_ind}"
                        try:
                            req_val = urllib.request.Request(url_val, method="GET")
                            with urllib.request.urlopen(req_val, timeout=2) as resp_val:
                                if resp_val.status == 200:
                                    val_data = json.loads(resp_val.read().decode("utf-8"))
                                    indicator_values[ind] = val_data.get("value")
                        except Exception:
                            indicator_values[ind] = "No disponible"
                            
                    orderflow_data.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "indicators": indicator_values
                    })
                return orderflow_data
    except Exception:
        return None

def analyze_market_top_down(yf_symbol):
    """Descarga y analiza de forma estructurada todas las 9 temporalidades de un mercado"""
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
        try:
            df_3m = df_1m.resample('3T').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna().tail(200)
            df_4m = df_1m.resample('4T').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna().tail(200)
        except Exception as e:
            print(f"Advertencia al resamplear LTF (3m/4m) para {yf_symbol}: {e}", file=sys.stderr)
            
    if df_1h is not None:
        try:
            df_4h = df_1h.resample('4H').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna().tail(200)
        except Exception as e:
            print(f"Advertencia al resamplear HTF (4H) para {yf_symbol}: {e}", file=sys.stderr)
            
    return {
        "4H": analyze_tf_structure(df_4h, swing_len=5),
        "1H": analyze_tf_structure(df_1h, swing_len=5),
        "30m": analyze_tf_structure(df_30m, swing_len=5),
        "15m": analyze_tf_structure(df_15m, swing_len=5),
        "5m": analyze_tf_structure(df_5m, swing_len=5),
        "4m": analyze_tf_structure(df_4m, swing_len=5),
        "3m": analyze_tf_structure(df_3m, swing_len=5),
        "2m": analyze_tf_structure(df_2m, swing_len=5),
        "1m": analyze_tf_structure(df_1m, swing_len=5),
        "df_2m": df_2m if df_2m is not None else df_5m,
        "last_price": float(df_2m["close"].iloc[-1]) if df_2m is not None else (float(df_5m["close"].iloc[-1]) if df_5m is not None else 0.0)
    }

def determine_relative_strength(mnq_analysis, mes_analysis):
    """Calcula matemáticamente cuál mercado es más fuerte/débil y define el bias local"""
    tfs = ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]
    
    mnq_bullish = sum(1 for tf in tfs if "Bullish" in mnq_analysis[tf]["bias"])
    mnq_bearish = sum(1 for tf in tfs if "Bearish" in mnq_analysis[tf]["bias"])
    
    mes_bullish = sum(1 for tf in tfs if "Bullish" in mes_analysis[tf]["bias"])
    mes_bearish = sum(1 for tf in tfs if "Bearish" in mes_analysis[tf]["bias"])
    
    # Pesos estructurales adicionales para marcos altos (HTF)
    mnq_weight = 0
    if "Bullish" in mnq_analysis["4H"]["bias"]: mnq_weight += 2
    if "Bullish" in mnq_analysis["1H"]["bias"]: mnq_weight += 1.5
    if "Bullish" in mnq_analysis["15m"]["bias"]: mnq_weight += 1.0
    if "Bearish" in mnq_analysis["4H"]["bias"]: mnq_weight -= 2
    if "Bearish" in mnq_analysis["1H"]["bias"]: mnq_weight -= 1.5
    if "Bearish" in mnq_analysis["15m"]["bias"]: mnq_weight -= 1.0
    
    mes_weight = 0
    if "Bullish" in mes_analysis["4H"]["bias"]: mes_weight += 2
    if "Bullish" in mes_analysis["1H"]["bias"]: mes_weight += 1.5
    if "Bullish" in mes_analysis["15m"]["bias"]: mes_weight += 1.0
    if "Bearish" in mes_analysis["4H"]["bias"]: mes_weight -= 2
    if "Bearish" in mes_analysis["1H"]["bias"]: mes_weight -= 1.5
    if "Bearish" in mes_analysis["15m"]["bias"]: mes_weight -= 1.0
    
    mnq_score = mnq_bullish - mnq_bearish + mnq_weight
    mes_score = mes_bullish - mes_bearish + mes_weight
    
    if mnq_score > mes_score:
        most_bullish = "Nasdaq (MNQ) 🟢"
        most_bearish = "S&P 500 (MES) 🔴"
        bias = "Bullish local (Nasdaq liderando)" if mnq_score > 0 else "Bearish local (Nasdaq resistiendo mejor)"
    elif mes_score > mnq_score:
        most_bullish = "S&P 500 (MES) 🟢"
        most_bearish = "Nasdaq (MNQ) 🔴"
        bias = "Bullish local (S&P 500 liderando)" if mes_score > 0 else "Bearish local (S&P 500 resistiendo mejor)"
    else:
        most_bullish = "Alineados por igual"
        most_bearish = "Alineados por igual"
        bias = "Neutral / Sincronía Completa"
        
    return bias, most_bullish, most_bearish, mnq_score, mes_score

def process_manual_drawings(drawings_list, tf_analysis, last_price):
    """Compara las marcaciones manuales extraídas con los niveles calculados por SMC en el código"""
    confluences = []
    manual_rectangles = []
    manual_lines = []
    
    for s in drawings_list:
        name = s.get("name", "")
        pts = s.get("points")
        props = s.get("properties", {})
        
        if not pts or len(pts) < 1:
            continue
            
        if name == "rectangle":
            p1 = pts[0].get("price")
            p2 = pts[1].get("price") if len(pts) > 1 else p1
            if p1 is not None and p2 is not None:
                bottom = min(p1, p2)
                top = max(p1, p2)
                text = props.get("text", "")
                manual_rectangles.append({
                    "id": s.get("id"),
                    "bottom": bottom,
                    "top": top,
                    "text": text,
                    "color": props.get("backgroundColor", "rgba(156,156,156,0.2)")
                })
        elif name in ["trend_line", "horizontal_line", "ray", "extended_line"]:
            p1 = pts[0].get("price")
            p2 = pts[1].get("price") if len(pts) > 1 else p1
            if p1 is not None:
                manual_lines.append({
                    "id": s.get("id"),
                    "name": name,
                    "price_start": p1,
                    "price_end": p2,
                    "text": props.get("text", ""),
                    "color": props.get("linecolor", "#808080")
                })
                
    for rect in manual_rectangles:
        overlaps = []
        for tf in ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]:
            tf_data = tf_analysis[tf]
            for ob in tf_data.get("obs", []):
                ob_bottom = ob["bottom"]
                ob_top = ob["top"]
                if max(rect["bottom"], ob_bottom) < min(rect["top"], ob_top):
                    overlaps.append(f"**OB {tf}** ({ob_bottom:.1f} - {ob_top:.1f})")
            for fvg in tf_data.get("fvgs", []):
                fvg_bottom = fvg["bottom"]
                fvg_top = fvg["top"]
                if max(rect["bottom"], fvg_bottom) < min(rect["top"], fvg_top):
                    overlaps.append(f"**FVG {tf}** ({fvg_bottom:.1f} - {fvg_top:.1f})")
                    
        is_inside = rect["bottom"] <= last_price <= rect["top"]
        status = "🟢 PRECIO DENTRO" if is_inside else "🟡 Fuera del precio"
        label_text = f" con etiqueta '{rect['text']}'" if rect["text"] else ""
        overlap_str = f" | Confluencias: {', '.join(overlaps)}" if overlaps else " | Sin confluencia SMC directa"
        confluences.append(
            f"  * **Caja Gris{label_text}** en rango `{rect['bottom']:.2f} - {rect['top']:.2f}` | Estado: {status}{overlap_str}"
        )
        
    for line in manual_lines:
        dist_start = abs(last_price - line["price_start"])
        near_start = dist_start < 25
        status = "🎯 PRECIO CERCA" if near_start else "Fuera de rango"
        label_text = f" con etiqueta '{line['text']}'" if line["text"] else ""
        
        overlaps = []
        for tf in ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]:
            tf_data = tf_analysis[tf]
            for ob in tf_data.get("obs", []):
                if ob["bottom"] <= line["price_start"] <= ob["top"]:
                    overlaps.append(f"dentro de **OB {tf}** ({ob['bottom']:.1f} - {ob['top']:.1f})")
            for fvg in tf_data.get("fvgs", []):
                if fvg["bottom"] <= line["price_start"] <= fvg["top"]:
                    overlaps.append(f"dentro de **FVG {tf}** ({fvg['bottom']:.1f} - {fvg['top']:.1f})")
                    
        conf_str = f" | Ubicación: {', '.join(overlaps)}" if overlaps else ""
        confluences.append(
            f"  * **Línea Manual{label_text}** en nivel `{line['price_start']:.2f}` | Estado: {status}{conf_str}"
        )
        
    return confluences

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    print("Iniciando escáner de Confluencias Avanzadas Premarket (Multi-Market & Multi-TF)...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    analyze_journal_path = os.path.join(script_dir, "analyze_journal.py")
    if os.path.exists(analyze_journal_path):
        print("Retroalimentando red neuronal: leyendo historial de bitácoras de Obsidian...")
        subprocess.run([sys.executable, analyze_journal_path], capture_output=True, text=True)
        
    mcp_cli_path = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
    
    # 1. Obtener estado original del gráfico
    state_result = subprocess.run(
        ["node", mcp_cli_path, "status"],
        capture_output=True,
        text=True
    )
    
    use_fallback = False
    orig_symbol = "CME_MINI:MNQ1!"
    orig_resolution = "2"
    
    if state_result.returncode != 0:
        print("Advertencia: No se pudo conectar con TradingView Desktop. Usando modo de contingencia (Yahoo Finance)...")
        use_fallback = True
    else:
        try:
            state_data = json.loads(state_result.stdout)
            if not state_data.get("success") or not state_data.get("cdp_connected"):
                print("Advertencia: CDP inactivo. Usando modo de contingencia...")
                use_fallback = True
            else:
                orig_symbol = state_data.get("chart_symbol", "CME_MINI:MNQ1!")
                orig_resolution = state_data.get("chart_resolution", "2")
        except Exception:
            print("Advertencia: Error al leer estado de TradingView. Usando modo de contingencia...")
            use_fallback = True

    # 2. Navegación multitemporal y extracción de marcaciones por CDP (1m a 4H) para MNQ y MES
    drawings_by_market = {
        "MNQ": [],
        "MES": []
    }
    
    market_symbols = {
        "MNQ": "CME_MINI:MNQ1!",
        "MES": "CME_MINI:MES1!"
    }
    
    tf_map = {
        "4H": "240", "1H": "60", "30m": "30", "15m": "15",
        "5m": "5", "4m": "4", "3m": "3", "2m": "2", "1m": "1"
    }
    
    if not use_fallback:
        print("CDP ACTIVO: Iniciando recorrido multitemporal automatizado en TradingView...")
        try:
            for mkt_key, mkt_sym in market_symbols.items():
                print(f"Cambiando gráfico a {mkt_sym}...")
                subprocess.run(["node", mcp_cli_path, "symbol", mkt_sym], capture_output=True)
                time.sleep(1.2) # Tiempo de carga del símbolo
                
                for tf_name, tf_val in tf_map.items():
                    print(f" -> Escaneando temporalidad {tf_name} ({tf_val}m)...")
                    subprocess.run(["node", mcp_cli_path, "timeframe", tf_val], capture_output=True)
                    time.sleep(0.8) # Esperar a que renderice y carguen los dibujos del usuario
                    
                    # Evaluar shapes en el chart
                    js_get_drawings = r"(function(){try{var api=window.TradingViewApi._activeChartWidgetWV.value();var all=api.getAllShapes();var drawings=[];for(var i=0;i<all.length;i++){var s=all[i];var shape=api.getShapeById(s.id);if(shape){var pts=null;try{pts=shape.getPoints();}catch(e){}if(!pts){try{pts=shape.points();}catch(e){}}var props=null;try{props=shape.getProperties();}catch(e){}if(!props){try{props=shape.properties();}catch(e){}}drawings.push({id:s.id,name:s.name,points:pts,properties:props});}}return {success:true,drawings:drawings};}catch(e){return {success:false,error:e.message};}})()"
                    drawings_eval = subprocess.run(
                        ["node", mcp_cli_path, "ui", "eval", js_get_drawings],
                        capture_output=True,
                        text=True
                    )
                    
                    if drawings_eval.returncode == 0:
                        try:
                            draw_data = json.loads(drawings_eval.stdout)
                            shapes = []
                            if draw_data.get("success"):
                                if "result" in draw_data and isinstance(draw_data["result"], dict):
                                    shapes = draw_data["result"].get("drawings", [])
                                else:
                                    shapes = draw_data.get("drawings", [])
                            for s in shapes:
                                s["timeframe"] = tf_name
                                drawings_by_market[mkt_key].append(s)
                        except Exception as e:
                            print(f"Error al decodificar dibujos en {mkt_key} {tf_name}: {e}", file=sys.stderr)
            
            # Restaurar el estado original del gráfico
            print(f"Restaurando gráfico original a {orig_symbol} [{orig_resolution}m]...")
            subprocess.run(["node", mcp_cli_path, "symbol", orig_symbol], capture_output=True)
            time.sleep(1.0)
            subprocess.run(["node", mcp_cli_path, "timeframe", orig_resolution], capture_output=True)
            
        except Exception as ex:
            print(f"Error durante la automatización del gráfico: {ex}", file=sys.stderr)
            use_fallback = True
            
    else:
        print("Aviso: Omitiendo extracción de dibujos CDP (modo contingencia activo).")
        
    # 3. Descarga y análisis Top-Down completo en segundo plano para AMBOS mercados
    print("Descargando datos históricos de Yahoo Finance...")
    mnq_analysis = analyze_market_top_down("MNQ=F")
    mes_analysis = analyze_market_top_down("MES=F")
    
    # 4. Calcular el sesgo y la fuerza relativa inter-mercado
    bias_local, most_bullish, most_bearish, mnq_score, mes_score = determine_relative_strength(mnq_analysis, mes_analysis)
    
    # 5. Obtener alerta SMT en vivo
    smt_result = check_smt_divergence()
    
    # Obtener confluencias de Order Flow de NinjaTrader
    print("Consultando confluencias de Order Flow desde NinjaTrader...")
    orderflow_data = get_ninjatrader_orderflow()
    
    # 6. Procesar confluencias para las marcaciones manuales recopiladas
    mnq_confluences = process_manual_drawings(drawings_by_market["MNQ"], mnq_analysis, mnq_analysis["last_price"])
    mes_confluences = process_manual_drawings(drawings_by_market["MES"], mes_analysis, mes_analysis["last_price"])
    
    # 7. Reglas de Gatillos y Filtros Negativos (Qué debe pasar y cuándo NO operar)
    # Long triggers
    long_triggers = (
        f"1. **Barrida de Liquidez Estructural (Sweep):** El precio de {most_bullish.split(' ')[0]} debe barrer liquidez externa inferior "
        f"(mínimo de sesión previa o swing low local en {mnq_analysis['15m']['obs'][0]['bottom']:.1f} o similar) en temporalidad intermedia.\n"
        f"2. **Desplazamiento y Confirmación (iFVG):** Tras barrer liquidez, el precio debe desplazarse fuereña en el gráfico LTF (1m-5m) "
        f"y cerrar con cuerpo completo por encima de un FVG bajista, convirtiéndolo en un Inverse FVG (iFVG).\n"
        f"3. **Perfil de Entrada Preferente:** Priorizar perfiles G-R-G (Fáciles de Invertir) para validar el orderflow alcista con momentum."
    )
    # Short triggers
    short_triggers = (
        f"1. **Barrida de Liquidez Estructural (Sweep):** El precio de {most_bearish.split(' ')[0]} debe barrer liquidez externa superior "
        f"(máximo de sesión previa o swing high local) y mitigar una zona de resistencia de Oferta.\n"
        f"2. **Desplazamiento y Confirmación (iFVG):** Reacción impulsiva bajista en LTF que rompa y cierre por debajo de un FVG alcista "
        f"(perfil R-G-R preferente) para validar la inversión institucional a iFVG.\n"
        f"3. **Alineación de Fuerza:** Entrar en short en el mercado más débil para maximizar la velocidad de la caída."
    )
    # Bad idea for longs
    bad_long = (
        f"1. **Premium HTF:** Si el precio de MNQ o MES está cotizando dentro de zona Premium del rango de 1H/30m.\n"
        f"2. **Mitigación Hostil:** Si el precio está chocando directamente con una resistencia fuerte o Supply OB de 1H/4H.\n"
        f"3. **Divergencia SMT Bajista:** Si detectamos divergencia SMT Bajista (S&P 500 hace altos más altos pero Nasdaq falla en hacerlos), "
        f"lo que indica distribución institucional activa."
    )
    # Bad idea for shorts
    bad_short = (
        f"1. **Discount HTF:** Si el precio se encuentra cotizando en zona de descuento estructural (Discount) de 1H/30m.\n"
        f"2. **Soporte Hostil:** Si el precio se apoya en un Demand OB de 1H/4H inmitigado.\n"
        f"3. **Divergencia SMT Alcista:** Si detectamos divergencia SMT Alcista (S&P 500 barre mínimos pero Nasdaq sostiene mínimos más altos), "
        f"lo que indica acumulación e invalida ventas."
    )

    # 8. Cargar perfil psicológico del Guardia de Riesgo
    psych_profile_path = os.path.join(script_dir, "psych_profile.json")
    psych_data = None
    if os.path.exists(psych_profile_path):
        try:
            with open(psych_profile_path, "r", encoding="utf-8") as pf:
                psych_data = json.load(pf)
        except Exception:
            pass

    # 9. Clasificación ML para ambos mercados
    ml_classifier_path = os.path.join(script_dir, "ml_setup_classifier.py")
    ml_result_mnq = ""
    ml_result_mes = ""
    if os.path.exists(ml_classifier_path):
        def run_ml_predict(inst, bias_val, has_bpr, has_fvg, has_ob):
            confs = ["kz"]
            if has_bpr: confs.append("bpr")
            if has_fvg: confs.append("fvg")
            if has_ob: confs.append("ob")
            if smt_result and "DETECTADO" in smt_result: confs.append("smt")
            if bias_val != "Neutral": confs.append("bias")
            confs_str = ",".join(confs)
            direction = "Long" if "Bullish" in bias_val else "Short" if "Bearish" in bias_val else "Long"
            try:
                res = subprocess.run(
                    [sys.executable, ml_classifier_path, "--predict", "--inst", inst, "--dir", direction, "--sess", "NY AM KZ", "--confs", confs_str],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                if res.returncode == 0:
                    return res.stdout.strip()
            except Exception:
                pass
            return ""
            
        ml_result_mnq = run_ml_predict("NQ", mnq_analysis["1H"]["bias"], len(mnq_analysis["2m"]["fvgs"]) > 0, len(mnq_analysis["2m"]["fvgs"]) > 0, len(mnq_analysis["2m"]["obs"]) > 0)
        ml_result_mes = run_ml_predict("ES", mes_analysis["1H"]["bias"], len(mes_analysis["2m"]["fvgs"]) > 0, len(mes_analysis["2m"]["fvgs"]) > 0, len(mes_analysis["2m"]["obs"]) > 0)

    # 10. Graficar en subplots: Izquierda MNQ, Derecha MES (Estética Premium)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    plt.style.use('dark_background')
    fig.patch.set_facecolor('#0f172a')
    
    def plot_market(ax, df_mkt, active_obs, active_fvgs, swings, title_name):
        ax.set_facecolor('#0f172a')
        # Graficar velas
        for i in range(len(df_mkt)):
            open_p = df_mkt["open"].iloc[i]
            high_p = df_mkt["high"].iloc[i]
            low_p = df_mkt["low"].iloc[i]
            close_p = df_mkt["close"].iloc[i]
            
            color = '#22c55e' if close_p >= open_p else '#ef4444'
            ax.vlines(i, low_p, high_p, color=color, linewidth=1.2)
            rect = patches.Rectangle(
                (i - 0.35, min(open_p, close_p)),
                0.7,
                abs(close_p - open_p),
                facecolor=color,
                edgecolor=color,
                alpha=0.9
            )
            ax.add_patch(rect)
            
        # OBs
        for _, row in active_obs.iterrows():
            ob_start = int(row.name)
            ob_end = len(df_mkt) - 1
            ob_color = '#10b981' if row["OB"] == 1 else '#f43f5e'
            ob_text = "Bull OB" if row["OB"] == 1 else "Bear OB"
            rect = patches.Rectangle(
                (ob_start, row["Bottom"]),
                ob_end - ob_start,
                row["Top"] - row["Bottom"],
                facecolor=ob_color,
                edgecolor=ob_color,
                alpha=0.12,
                linestyle='--',
                linewidth=0.8
            )
            ax.add_patch(rect)
            ax.hlines(row["Top"], ob_start, ob_end, colors=ob_color, linestyles='dashed', linewidth=0.5)
            ax.hlines(row["Bottom"], ob_start, ob_end, colors=ob_color, linestyles='dashed', linewidth=0.5)
            # Add text label for OB
            ax.text(ob_start + 1, (row["Top"] + row["Bottom"])/2, ob_text, color=ob_color, fontsize=7, fontweight='bold', alpha=0.8, va='center')
            
        # FVGs
        for idx, row in active_fvgs.iterrows():
            fvg_color = '#06b6d4' if row["FVG"] == 1 else '#eab308'
            fvg_text = "Bull FVG" if row["FVG"] == 1 else "Bear FVG"
            rect = patches.Rectangle(
                (idx, row["Bottom"]),
                len(df_mkt) - 1 - idx,
                row["Top"] - row["Bottom"],
                facecolor=fvg_color,
                edgecolor=fvg_color,
                alpha=0.08,
                linestyle=':',
                linewidth=0.5
            )
            ax.add_patch(rect)
            # Add text label for FVG
            ax.text(idx + 1, (row["Top"] + row["Bottom"])/2, fvg_text, color=fvg_color, fontsize=7, fontweight='bold', alpha=0.8, va='center')
            
        # Estilos generales
        ax.set_title(title_name, fontsize=14, color='#f8fafc', pad=10)
        ax.set_xlabel("Velas Recientes", color='#94a3b8')
        ax.set_ylabel("Precio", color='#94a3b8')
        ax.tick_params(colors='#94a3b8', labelsize=8)
        ax.grid(True, color='#334155', alpha=0.3, linestyle=':')
        for spine in ax.spines.values():
            spine.set_color('#1e293b')

    # Graficar MNQ
    df_mnq_2m = mnq_analysis["df_2m"]
    swings_nq = smc.swing_highs_lows(df_mnq_2m, swing_length=5)
    obs_nq = smc.ob(df_mnq_2m, swings_nq)
    fvgs_nq = smc.fvg(df_mnq_2m)
    active_obs_nq = obs_nq[obs_nq["OB"].notna() & (obs_nq["OB"] != 0) & ((obs_nq["MitigatedIndex"] == 0) | obs_nq["MitigatedIndex"].isna())]
    active_fvgs_nq = fvgs_nq[fvgs_nq["FVG"].notna() & (fvgs_nq["FVG"] != 0) & ((fvgs_nq["MitigatedIndex"] == 0) | fvgs_nq["MitigatedIndex"].isna())]
    plot_market(ax1, df_mnq_2m, active_obs_nq, active_fvgs_nq, swings_nq, f"Nasdaq (MNQ) 2m - Price: {mnq_analysis['last_price']:.2f}")

    # Graficar MES
    df_mes_2m = mes_analysis["df_2m"]
    swings_es = smc.swing_highs_lows(df_mes_2m, swing_length=5)
    obs_es = smc.ob(df_mes_2m, swings_es)
    fvgs_es = smc.fvg(df_mes_2m)
    active_obs_es = obs_es[obs_es["OB"].notna() & (obs_es["OB"] != 0) & ((obs_es["MitigatedIndex"] == 0) | obs_es["MitigatedIndex"].isna())]
    active_fvgs_es = fvgs_es[fvgs_es["FVG"].notna() & (fvgs_es["FVG"] != 0) & ((fvgs_es["MitigatedIndex"] == 0) | fvgs_es["MitigatedIndex"].isna())]
    plot_market(ax2, df_mes_2m, active_obs_es, active_fvgs_es, swings_es, f"S&P 500 (MES) 2m - Price: {mes_analysis['last_price']:.2f}")

    # Guardar gráficos en sus rutas
    today_str = time.strftime("%Y-%m-%d")
    journal_dir = os.path.dirname(script_dir)
    bitacoras_dir = os.path.join(journal_dir, "bitacoras")
    imagenes_dir = os.path.join(journal_dir, "imagenes")
    os.makedirs(bitacoras_dir, exist_ok=True)
    os.makedirs(imagenes_dir, exist_ok=True)
    
    workspace_img_path = os.path.join(imagenes_dir, f"{today_str}_pre_trade_dual.png")
    
    # Ruta del artefacto actual de Gemini
    artifact_dir = r"C:\Users\rsama\AppData\Local\Temp" # Fallback temporal
    # Buscamos el workspace actual de Gemini por la ruta del prompt
    gemini_workspace = r"C:\Users\rsama\.gemini\antigravity-cli\brain\02cb9977-937b-410d-8eb5-107b2e6261c9"
    if os.path.exists(gemini_workspace):
        artifact_dir = gemini_workspace
        
    gemini_img_path = os.path.join(artifact_dir, "smc_analysis.png")
    gemini_report_path = os.path.join(artifact_dir, "smc_analysis_report.md")
    
    plt.tight_layout()
    plt.savefig(workspace_img_path, dpi=150, facecolor='#0f172a')
    plt.savefig(gemini_img_path, dpi=150, facecolor='#0f172a')
    plt.close()

    # 11. Generar e invocar el reporte Markdown
    def self_generate_vwap_guidance(bias_local, mnq_score, mes_score, orderflow_data):
        is_trend_day = False
        if orderflow_data:
            for item in orderflow_data:
                for ind_name, val in item["indicators"].items():
                    if "cumulative delta" in ind_name.lower() and val is not None:
                        try:
                            if abs(float(val)) > 3000:
                                is_trend_day = True
                        except:
                            pass
        if "bullish" in bias_local.lower() or "bearish" in bias_local.lower():
            if abs(mnq_score) > 5 or abs(mes_score) > 5:
                is_trend_day = True

        if is_trend_day:
            return """* **Estado de Mercado Esperado:** **Día de Tendencia (Expansión) 🚀**
* **Guía Operativa del VWAP:**
  * **El Premium/Discount de altas temporalidades deja de importar y la media del VWAP también.**
  * Concéntrate más en las **Bandas de Desviación Estándar 2 y 3**, ya que el precio tenderá a caminar y sostenerse sobre ellas a favor de la tendencia.
  * **⚠️ ADVERTENCIA:** Está estrictamente prohibido usar las bandas externas de +2 o +3 desviaciones para buscar contratendencias (cortos si sube, largos si cae); el precio tenderá a "caminar" sobre ellas."""
        else:
            return """* **Estado de Mercado Esperado:** **Día de Rango (Consolidación) 🔄**
* **Guía Operativa del VWAP:**
  * El precio tenderá a regresar constantemente a la línea media (VWAP central).
  * Busca compras únicamente en la **Banda Inferior de -2 Desviaciones** y ventas en la **Banda Superior de +2 Desviaciones** cuando confluyan con barridas de liquidez de micro-temporalidad.
  * Evita buscar continuaciones largas. Mantén objetivos cortos y toma ganancias al regresar a la línea del VWAP."""

    def generate_md_report(f, img_path, orderflow_data):
        tfs = ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]
        f.write(f"""# 🛠️ Reporte Pre-Trade Avanzado: Mapa Dual de Confluencias (MNQ & MES)

Este reporte evalúa la estructura de mercado y dibuja la confluencia entre tus marcas de TradingView recopiladas vía CDP a lo largo de las 9 temporalidades analizadas en Nasdaq (`MNQ`) y S&P 500 (`MES`).

---

## 📅 Información de la Sesión
* **Fecha:** `{today_str}`
* **Mercados Analizados:** Nasdaq (MNQ) y S&P 500 (MES)
* **Precios de Referencia:** MNQ: `{mnq_analysis['last_price']:.2f}` | MES: `{mes_analysis['last_price']:.2f}`
* **Vinculación Temporal:** 
  * 🔗 [Ver Autopsia y Bitácora Post-Trade de esta Sesión]({today_str}_session.md) (Se generará al finalizar tu sesión)

---

## ⚖️ Análisis de Bias y Fuerza Relativa
* **Bias Local Dominante:** `{bias_local}`
* **Mercado Más Alcista (Fuerte):** `{most_bullish}`
* **Mercado Más Bajista (Débil):** `{most_bearish}`
* **Puntuación de Fuerza ESTRUCTURAL:** NQ Score: `{mnq_score}` | ES Score: `{mes_score}`

---

## 🌊 Confluencias de Order Flow (NinjaTrader 8)
""")
        if not orderflow_data:
            f.write("* ⚠️ **Servidor de NinjaTrader inactivo o sin gráficos abiertos.** Asegúrate de abrir NinjaTrader 8 con tu gráfico e indicadores de Order Flow activos para enriquecer este reporte.*\n")
        else:
            for item in orderflow_data:
                f.write(f"### 📊 Gráfico Activo: `{item['symbol']}` ({item['timeframe']})\n")
                if not item["indicators"]:
                    f.write("  * *No se detectaron indicadores de Order Flow (Cumulative Delta, Volumen, etc.) en este gráfico.*\n")
                else:
                    for ind_name, val in item["indicators"].items():
                        val_str = f"`{val}`" if val is not None else "`null`"
                        bias_note = ""
                        if "cumulative delta" in ind_name.lower():
                            if val is not None and val != "No disponible":
                                try:
                                    val_num = float(val)
                                    if val_num > 0:
                                        bias_note = " ➔ **Presión Compradora a Mercado (Alcista) 🟢**"
                                    elif val_num < 0:
                                        bias_note = " ➔ **Presión Vendedora a Mercado (Bajista) 🔴**"
                                except Exception:
                                    pass
                        f.write(f"  * **{ind_name}**: {val_str}{bias_note}\n")
                        
        f.write(f"""
---

## 📈 Tabla Comparativa de Estructura (Multi-Temporalidad)

| Temporalidad | Sesgo MNQ | Rango MNQ | Sesgo MES | Rango MES |
| :--- | :--- | :--- | :--- | :--- |
""")
        for tf in tfs:
            mnq_tf = mnq_analysis[tf]
            mes_tf = mes_analysis[tf]
            f.write(f"| **{tf}** | {mnq_tf.get('bias', 'Neutral')} | {mnq_tf.get('range_state', 'Desconocido')} | {mes_tf.get('bias', 'Neutral')} | {mes_tf.get('range_state', 'Desconocido')} |\n")

        f.write(f"""
---

## 🛡️ Alerta del Guardia de Riesgo (IA Risk Mentor)
""")
        if psych_data:
            f.write(f"""
> [!IMPORTANT]
> **Estadísticas de Bitácora:** Sesiones: `{psych_data['total_sessions']}` | PnL Acumulado: `${psych_data['total_pnl']:.2f} USD` | Win Rate: `{psych_data['win_rate_sessions']}%`
> 
> **🚨 TUS ERRORES PSICOLÓGICOS MÁS RECURRENTES A EVITAR HOY:**
""")
            for warn in psych_data["warnings"][:2]:
                f.write(f"> * **{warn['error']}:** presente en el `{warn['percentage']}%` de las sesiones previas.\n")
            f.write(">\n> **📝 LECCIONES CLAVE A RECORDAR:**\n")
            for les in psych_data["recent_lessons"][-3:]:
                f.write(f"> * {les}\n")
        else:
            f.write("> [!NOTE]\n> Aún no se han detectado perfiles psicológicos previos. Las autopsias en Obsidian alimentan la retroalimentación de riesgo de manera pasiva.\n")

        f.write(f"""
---

## 🎯 Plan Operativo de Sesión (Gatillos Estructurales)

### 🟢 Escenario para LONG (Compras)
{long_triggers}

### 🔴 Escenario para SHORT (Ventas)
{short_triggers}

---

## 🚫 Filtros Negativos (Zonas de Peligro)

### ⚠️ Mala Idea Tirar LONGS (No Comprar)
{bad_long}

### ⚠️ Mala Idea Tirar SHORTS (No Vender)
{bad_short}

---

## 🌀 Estrategia de VWAP y Nivel de Liquidez (DOL)
{self_generate_vwap_guidance(bias_local, mnq_score, mes_score, orderflow_data)}

---

## ⚡ Correlación Inter-Mercado (SMT Divergence)
* **Estado SMT:** `{smt_result if smt_result else 'S&P 500 (MES) y Nasdaq (MNQ) alineados de forma regular en el Open (Sin divergencias activas).'}`

---

## 🧠 Predicciones de Machine Learning (Win Rate Classifier)
""")
        if ml_result_mnq:
            f.write(f"### 💻 Predicción Nasdaq (MNQ):\n```text\n{ml_result_mnq}\n```\n")
        if ml_result_mes:
            f.write(f"### 📊 Predicción S&P 500 (MES):\n```text\n{ml_result_mes}\n```\n")

        f.write(f"""
---

## 🎨 Comparación con Marcaciones Manuales (TradingView CDP)

### 💻 Marcaciones en Nasdaq (MNQ) por Temporalidad:
""")
        if len(mnq_confluences) == 0:
            f.write("  * *No se detectaron marcaciones manuales en Nasdaq.* Asegúrate de graficar en TradingView.\n")
        else:
            for conf in mnq_confluences:
                f.write(f"{conf}\n")

        f.write(f"""
### 📊 Marcaciones en S&P 500 (MES) por Temporalidad:
""")
        if len(mes_confluences) == 0:
            f.write("  * *No se detectaron marcaciones manuales en S&P 500.* Asegúrate de graficar en TradingView.\n")
        else:
            for conf in mes_confluences:
                f.write(f"{conf}\n")

        f.write(f"""
---

## 🖼️ Mapa Visual de Estructuras (2m)

![Gráfico Dual de Confluencias]({img_path})
""")

    # Escribir reporte en Obsidian
    workspace_report_path = os.path.join(bitacoras_dir, f"{today_str}_pre_trade.md")
    with open(workspace_report_path, "w", encoding="utf-8") as f:
        generate_md_report(f, f"../imagenes/{today_str}_pre_trade_dual.png", orderflow_data)

    # Escribir reporte espejo en Gemini
    with open(gemini_report_path, "w", encoding="utf-8") as f:
        generate_md_report(f, f"file:///{gemini_img_path.replace(chr(92), '/')}", orderflow_data)

    print(f"\n=========================================================")
    print("=== REPORTE DE BIAS Y ESTRATEGIA PRE-TRADE DUAL ===")
    print("=========================================================")
    print(f"Bias Local: {bias_local}")
    print(f"Mercado fuerte (Bullish): {most_bullish}")
    print(f"Mercado débil (Bearish): {most_bearish}")
    if smt_result:
        print(f"Alerta Divergencia SMT: {smt_result}")
    else:
        print("Sincronía SMT: S&P 500 y Nasdaq alineados.")
        
    if orderflow_data:
        print("\n--- CONFLUENCIAS DE ORDER FLOW (NinjaTrader 8) ---")
        for item in orderflow_data:
            print(f"Gráfico: {item['symbol']} ({item['timeframe']})")
            for ind, val in item["indicators"].items():
                print(f"  * {ind}: {val}")
        
    print("\n--- GATILLO LONG ---")
    print(long_triggers)
    print("\n--- GATILLO SHORT ---")
    print(short_triggers)
    print("\n--- MALA IDEA LONG ---")
    print(bad_long)
    print("\n--- MALA IDEA SHORT ---")
    print(bad_short)
    print("=========================================================")
    print(f"Reporte de sesión guardado con éxito en: {workspace_report_path}")
    print(f"Reporte espejo Gemini actualizado en: {gemini_report_path}")

if __name__ == "__main__":
    main()
