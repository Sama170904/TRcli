import os
os.environ["SMC_CREDIT"] = "0"
import sys
import json
import subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from smartmoneyconcepts import smc
import yfinance as yf

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
        print(f"Advertencia al descargar temporalidad HTF ({interval}): {e}", file=sys.stderr)
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
        # Descargar últimos datos de 2m para MNQ y MES de Yahoo Finance (usamos 5d para robustez en fines de semana)
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
        
        # Calcular swings en ambos activos
        swings_nq = smc.swing_highs_lows(df_nq, swing_length=3)
        swings_es = smc.swing_highs_lows(df_es, swing_length=3)
        
        # Buscar últimos swings de bajos significativos
        lows_nq = swings_nq[swings_nq["HighLow"] == -1].tail(2)
        lows_es = swings_es[swings_es["HighLow"] == -1].tail(2)
        
        # Buscar últimos swings de altos significativos
        highs_nq = swings_nq[swings_nq["HighLow"] == 1].tail(2)
        highs_es = swings_es[swings_es["HighLow"] == 1].tail(2)
        
        # SMT Alcista (Bullish SMT): NQ Higher Low (HL) mientras ES Lower Low (LL)
        if len(lows_nq) >= 2 and len(lows_es) >= 2:
            nq_l1, nq_l2 = lows_nq["Level"].iloc[-2], lows_nq["Level"].iloc[-1]
            es_l1, es_l2 = lows_es["Level"].iloc[-2], lows_es["Level"].iloc[-1]
            if nq_l2 > nq_l1 and es_l2 < es_l1:
                return "SMT ALCISTA DETECTADO 🟢 (Nasdaq sostiene mínimos más altos mientras S&P barre a mínimos más bajos. ¡Acumulación institucional!)"
                
        # SMT Bajista (Bearish SMT): NQ Lower High (LH) mientras ES Higher High (HH)
        if len(highs_nq) >= 2 and len(highs_es) >= 2:
            nq_h1, nq_h2 = highs_nq["Level"].iloc[-2], highs_nq["Level"].iloc[-1]
            es_h1, es_h2 = highs_es["Level"].iloc[-2], highs_es["Level"].iloc[-1]
            if nq_h2 < nq_h1 and es_h2 > es_h1:
                return "SMT BAJISTA DETECTADO 🔴 (Nasdaq hace máximos más bajos mientras S&P expande a máximos más altos. ¡Distribución institucional!)"
                
        return None
    except Exception as e:
        return f"Advertencia SMT: No se pudo conectar a los servidores de datos de S&P 500: {e}"

def main():
    # Asegurar codificación UTF-8 en consola para evitar caídas por emojis en Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    print("Iniciando escáner de Confluencias Avanzadas Pre-Trade...")
    
    # 0. Ejecutar el analizador de bitácoras para retroalimentar la red neuronal en vivo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    analyze_journal_path = os.path.join(script_dir, "analyze_journal.py")
    if os.path.exists(analyze_journal_path):
        print("Retroalimentando red neuronal: leyendo historial de bitácoras de Obsidian...")
        subprocess.run([sys.executable, analyze_journal_path], capture_output=True, text=True)
        
    # Ruta absoluta al CLI de TradingView MCP
    mcp_cli_path = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"
    
    # 1. Obtener el estado del gráfico
    state_result = subprocess.run(
        ["node", mcp_cli_path, "status"],
        capture_output=True,
        text=True
    )
    
    use_fallback = False
    symbol = "MNQ=F"
    resolution = "2"
    
    if state_result.returncode != 0:
        print("Advertencia: No se pudo conectar con TradingView Desktop. Usando modo de contingencia (Yahoo Finance)...")
        use_fallback = True
    else:
        try:
            state_data = json.loads(state_result.stdout)
            if not state_data.get("success"):
                print("Advertencia: Estado de TradingView no disponible. Usando modo de contingencia...")
                use_fallback = True
            else:
                symbol = state_data.get("chart_symbol", "MNQ1!")
                resolution = state_data.get("chart_resolution", "2")
        except Exception:
            print("Advertencia: Error al descifrar estado de TradingView. Usando modo de contingencia...")
            use_fallback = True

    df = None
    if not use_fallback:
        print(f"Gráfico activo TradingView: {symbol} [{resolution}m]")
        n_bars = 150
        ohlcv_result = subprocess.run(
            ["node", mcp_cli_path, "ohlcv", "-n", str(n_bars)],
            capture_output=True,
            text=True
        )
        if ohlcv_result.returncode == 0:
            try:
                ohlcv_data = json.loads(ohlcv_result.stdout)
                if ohlcv_data.get("success"):
                    bars = ohlcv_data["bars"]
                    df = pd.DataFrame(bars)
                    for col in ["open", "high", "low", "close", "volume"]:
                        df[col] = df[col].astype(float)
            except Exception:
                pass
        if df is None:
            print("Advertencia: Falló la descarga desde TradingView. Intentando contingencia con Yahoo Finance...")
            use_fallback = True

    if use_fallback or df is None:
        yf_symbol = "MNQ=F"
        if "ES" in symbol.upper():
            yf_symbol = "MES=F"
        elif "GC" in symbol.upper():
            yf_symbol = "GC=F"
        elif "CL" in symbol.upper():
            yf_symbol = "CL=F"
            
        print(f"Modo Contingencia Activo: Descargando datos para {yf_symbol} en temporalidad de {resolution}m desde Yahoo Finance...")
        
        yf_interval = "2m"
        if resolution == "1": yf_interval = "1m"
        elif resolution == "5": yf_interval = "5m"
        elif resolution == "15": yf_interval = "15m"
        elif resolution == "30": yf_interval = "30m"
        elif resolution in ["60", "1h"]: yf_interval = "1h"
        
        df = fetch_htf_data(yf_symbol, interval=yf_interval, period="5d", count=150)
        if df is None or df.empty:
            print("Error fatal: No se pudieron obtener datos históricos del mercado de contingencia.", file=sys.stderr)
            sys.exit(1)
            
    last_price = df["close"].iloc[-1]
    
    # 3. Descarga y análisis de TODAS las temporalidades (Top-Down Completo: 1m a 4H)
    print("Iniciando análisis Top-Down Multitemporalidad Completo (1m a 4H) en segundo plano...")
    df_1m = fetch_htf_data("MNQ=F", interval="1m", period="2d", count=500)
    df_2m = fetch_htf_data("MNQ=F", interval="2m", period="5d", count=200)
    df_5m = fetch_htf_data("MNQ=F", interval="5m", period="5d", count=200)
    df_15m = fetch_htf_data("MNQ=F", interval="15m", period="5d", count=200)
    df_30m = fetch_htf_data("MNQ=F", interval="30m", period="10d", count=200)
    df_1h = fetch_htf_data("MNQ=F", interval="1h", period="30d", count=200)
    
    # Resamplear temporalidades faltantes (3m, 4m y 4H) para evadir limitaciones de yfinance
    df_3m = None
    df_4m = None
    df_4h = None
    
    if df_1m is not None:
        try:
            df_3m = df_1m.resample('3T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().tail(200)
            df_4m = df_1m.resample('4T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().tail(200)
        except Exception as e:
            print(f"Advertencia al resamplear LTF (3m/4m): {e}", file=sys.stderr)
            
    if df_1h is not None:
        try:
            df_4h = df_1h.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().tail(200)
        except Exception as e:
            print(f"Advertencia al resamplear HTF (4H): {e}", file=sys.stderr)
            
    # Analizar todas las temporalidades estructurales
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

    # Redefinir htf_analysis para mantener compatibilidad hacia atrás
    htf_analysis = {
        "4H": all_tf_analysis["4H"],
        "1H": all_tf_analysis["1H"],
        "30m": all_tf_analysis["30m"],
        "15m": all_tf_analysis["15m"],
        "5m": all_tf_analysis["5m"],
        "4m": all_tf_analysis["4m"],
        "3m": all_tf_analysis["3m"],
        "2m": all_tf_analysis["2m"],
        "1m": all_tf_analysis["1m"],
        "1h": all_tf_analysis["1H"], # Alias para compatibilidad
    }
    
    # 4. Calcular Indicadores de Smart Money Concepts en LTF 2m
    swings = smc.swing_highs_lows(df, swing_length=5)
    obs = smc.ob(df, swings)
    fvgs = smc.fvg(df)
    bos_choch = smc.bos_choch(df, swings)
    liquidity_df = smc.liquidity(df, swings, range_percent=0.005)
    
    # Procesar Zonas Activas LTF 2m
    active_obs = obs[obs["OB"].notna() & (obs["OB"] != 0) & ((obs["MitigatedIndex"] == 0) | obs["MitigatedIndex"].isna())]
    active_fvgs = fvgs[fvgs["FVG"].notna() & (fvgs["FVG"] != 0) & ((fvgs["MitigatedIndex"] == 0) | fvgs["MitigatedIndex"].isna())]
    active_liquidity = liquidity_df[liquidity_df["Liquidity"].notna() & (liquidity_df["Liquidity"] != 0) & ((liquidity_df["Swept"] == 0) | liquidity_df["Swept"].isna() | (liquidity_df["Swept"] == 0.0))]
    recent_bos = bos_choch.dropna(subset=["BOS", "CHOCH"], how="all").tail(3)

    # 6. Calcular divergencia SMT en vivo (Opción 3)
    print("Calculando divergencia SMT contra S&P 500 en segundo plano...")
    smt_result = check_smt_divergence()
    
    # 7. Mapear Liquidez Externa (Últimos Swings LTF)
    swing_highs = swings[swings["HighLow"] == 1]
    swing_lows = swings[swings["HighLow"] == -1]
    last_swing_high = swing_highs.iloc[-1] if len(swing_highs) > 0 else None
    last_swing_low = swing_lows.iloc[-1] if len(swing_lows) > 0 else None
    
    # 8. Detectar BPR (Balanced Price Ranges - Solapamientos de FVG)
    bprs = []
    recent_bull_fvgs = fvgs[fvgs["FVG"] == 1].tail(10)
    recent_bear_fvgs = fvgs[fvgs["FVG"] == -1].tail(10)
    for idx_bull, r_bull in recent_bull_fvgs.iterrows():
        for idx_bear, r_bear in recent_bear_fvgs.iterrows():
            low_overlap = max(r_bull["Bottom"], r_bear["Bottom"])
            high_overlap = min(r_bull["Top"], r_bear["Top"])
            if low_overlap < high_overlap:
                bprs.append({
                    "bottom": low_overlap,
                    "top": high_overlap,
                    "bull_index": int(idx_bull),
                    "bear_index": int(idx_bear)
                })
                
    # 9. Formatear datos de FVG con su Perfil de 3 Velas
    formatted_fvgs = []
    for idx, row in active_fvgs.iterrows():
        fvg_type = int(row["FVG"])
        profile_str, inversion_prob = analyze_fvg_profile(df, idx, fvg_type)
        formatted_fvgs.append({
            "index": int(idx),
            "type": "Bullish" if fvg_type == 1 else "Bearish",
            "bottom": row["Bottom"],
            "top": row["Top"],
            "profile": profile_str,
            "inversion_prob": inversion_prob
        })
    # 9.5. Obtener dibujos manuales en tiempo real del gráfico TradingView a través de CDP
    user_shapes = []
    if not use_fallback:
        print("Obteniendo marcaciones manuales del usuario (líneas y rectángulos) desde TradingView...")
        js_get_drawings = r"(function(){try{var api=window.TradingViewApi._activeChartWidgetWV.value();var all=api.getAllShapes();var drawings=[];for(var i=0;i<all.length;i++){var s=all[i];var shape=api.getShapeById(s.id);if(shape){var pts=null;try{pts=shape.getPoints();}catch(e){}if(!pts){try{pts=shape.points();}catch(e){}}var props=null;try{props=shape.getProperties();}catch(e){}if(!props){try{props=shape.properties();}catch(e){}}drawings.push({id:s.id,name:s.name,points:pts,properties:props});}}return {success:true,drawings:drawings};}catch(e){return {success:false,error:e.message};}})()"
        
        drawings_eval = subprocess.run(
            ["node", mcp_cli_path, "ui", "eval", js_get_drawings],
            capture_output=True,
            text=True
        )
        
        if drawings_eval.returncode == 0:
            try:
                draw_data = json.loads(drawings_eval.stdout)
                if draw_data.get("success"):
                    if "result" in draw_data and isinstance(draw_data["result"], dict):
                        user_shapes = draw_data["result"].get("drawings", [])
                    else:
                        user_shapes = draw_data.get("drawings", [])
            except Exception as e:
                print(f"Advertencia al parsear dibujos manuales: {e}", file=sys.stderr)
    else:
        print("Aviso: Omitiendo marcaciones de TradingView (contingencia activa).")
            
    print(f"Se detectaron {len(user_shapes)} marcaciones manuales en tu gráfico.")
    
    manual_rectangles = []
    manual_lines = []
    
    for s in user_shapes:
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
                
    drawings_confluences = []
    for rect in manual_rectangles:
        overlaps = []
        for tf in ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]:
            tf_data = all_tf_analysis[tf]
            for ob in tf_data.get("obs", []):
                ob_type = "Demand OB" if ob["type"] == "Demand" else "Supply OB"
                ob_bottom = ob["bottom"]
                ob_top = ob["top"]
                if max(rect["bottom"], ob_bottom) < min(rect["top"], ob_top):
                    overlaps.append(f"**OB {tf}** ({ob_bottom:.1f} - {ob_top:.1f})")
            for fvg in tf_data.get("fvgs", []):
                fvg_type = "Bullish FVG" if fvg["type"] == "Bullish" else "Bearish FVG"
                fvg_bottom = fvg["bottom"]
                fvg_top = fvg["top"]
                if max(rect["bottom"], fvg_bottom) < min(rect["top"], fvg_top):
                    overlaps.append(f"**FVG {tf}** ({fvg_bottom:.1f} - {fvg_top:.1f})")
                    
        is_inside = rect["bottom"] <= last_price <= rect["top"]
        status = "🟢 PRECIO DENTRO" if is_inside else "🟡 Fuera del precio"
        label_text = f" con etiqueta '{rect['text']}'" if rect["text"] else ""
        overlap_str = f" | Confluencias: {', '.join(overlaps)}" if overlaps else " | Sin confluencia SMC directa"
        drawings_confluences.append(
            f"  * **Caja Gris{label_text}** en rango `{rect['bottom']:.2f} - {rect['top']:.2f}` | Estado: {status}{overlap_str}"
        )
        
    for line in manual_lines:
        dist_start = abs(last_price - line["price_start"])
        near_start = dist_start < 25
        status = "🎯 PRECIO CERCA" if near_start else "Fuera de rango"
        label_text = f" con etiqueta '{line['text']}'" if line["text"] else ""
        
        confluences = []
        for tf in ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]:
            tf_data = all_tf_analysis[tf]
            for ob in tf_data.get("obs", []):
                if ob["bottom"] <= line["price_start"] <= ob["top"]:
                    confluences.append(f"dentro de **OB {tf}** ({ob['bottom']:.1f} - {ob['top']:.1f})")
            for fvg in tf_data.get("fvgs", []):
                if fvg["bottom"] <= line["price_start"] <= fvg["top"]:
                    confluences.append(f"dentro de **FVG {tf}** ({fvg['bottom']:.1f} - {fvg['top']:.1f})")
                    
        conf_str = f" | Ubicación: {', '.join(confluences)}" if confluences else ""
        drawings_confluences.append(
            f"  * **Línea Manual{label_text}** en nivel `{line['price_start']:.2f}` | Estado: {status}{conf_str}"
        )

    # 10. Cargar Perfil de Riesgo Psicológico para la alerta del Guardia de Riesgo (Opción 2)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    psych_profile_path = os.path.join(script_dir, "psych_profile.json")
    psych_data = None
    if os.path.exists(psych_profile_path):
        try:
            with open(psych_profile_path, "r", encoding="utf-8") as pf:
                psych_data = json.load(pf)
        except Exception:
            pass

    # 10.5. Ejecutar la clasificación predictiva por Machine Learning (SMC Setup Classifier)
    ml_classifier_path = os.path.join(script_dir, "ml_setup_classifier.py")
    ml_result = ""
    if os.path.exists(ml_classifier_path):
        detected_confs = ["kz"]
        if len(bprs) > 0: detected_confs.append("bpr")
        if len(active_fvgs) > 0: detected_confs.append("fvg")
        if len(active_obs) > 0: detected_confs.append("ob")
        if smt_result and "DETECTADO" in smt_result: detected_confs.append("smt")
        if htf_analysis['1h']['bias'] != "Neutral": detected_confs.append("bias")
        
        confs_arg = ",".join(detected_confs)
        dir_arg = "Long" if "Bullish" in htf_analysis['1h']['bias'] else "Short" if "Bearish" in htf_analysis['1h']['bias'] else "Long"
        inst_arg = "ES" if "ES" in symbol.upper() else "NQ"
        
        try:
            res = subprocess.run(
                [sys.executable, ml_classifier_path, "--predict", "--inst", inst_arg, "--dir", dir_arg, "--sess", "NY AM KZ", "--confs", confs_arg],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0:
                ml_result = res.stdout.strip()
        except Exception as e:
            print(f"Advertencia al ejecutar el clasificador ML: {e}", file=sys.stderr)

    # Imprimir en consola de forma espectacular
    print("\n=========================================================")
    print("=== REPORTE AVANZADO PRE-TRADE: MAPA DE CONFLUENCIAS ===")
    print("=========================================================")
    print(f"Activo: {symbol} | Precio Actual: {last_price}")
    print(f"Sesgo Macro (1H HTF Bias): {htf_analysis['1h']['bias']}")
    
    if smt_result:
        print(f"\n⚡ ALERTA SMT: {smt_result}")
    else:
        print("\n⚡ SMT Correlation: S&P 500 y Nasdaq alineados de forma regular (Sin divergencia activa).")
        
    if last_swing_high is not None:
        print(f"Liquidez Externa Superior (Swing High): {last_swing_high['Level']} (Vela #{last_swing_high.name})")
    if last_swing_low is not None:
        print(f"Liquidez Externa Inferior (Swing Low): {last_swing_low['Level']} (Vela #{last_swing_low.name})")
        
    print("\n[Pools de Liquidez Interna (Unswept)]")
    for idx, row in active_liquidity.iterrows():
        liq_type = "Bullish (Highs) 🟢" if row["Liquidity"] == 1 else "Bearish (Lows) 🔴"
        print(f" * Pool de Liquidez {liq_type} en nivel {row['Level']} (Vela #{idx})")
        
    print("\n[Order Blocks Activos LTF 2m]")
    for idx, row in active_obs.iterrows():
        type_str = "Demand (🟢)" if row["OB"] == 1 else "Supply (🔴)"
        print(f" * OB {type_str} en {row['Bottom']} - {row['Top']} | Vol: {row['OBVolume']}")
        
    print("\n[FVGs Activos y Anatomía de Velas]")
    for fvg in formatted_fvgs:
        print(f" * FVG {fvg['type']} | Rango: {fvg['bottom']} - {fvg['top']} | Perfil: {fvg['profile']} ({fvg['inversion_prob']})")
        
    if len(bprs) > 0:
        print("\n[Balanced Price Ranges (BPR) Detectados]")
        for bpr in bprs[-3:]:
            print(f" * BPR Solapado en rango: {bpr['bottom']} - {bpr['top']} (FVG #{bpr['bull_index']} & #{bpr['bear_index']})")
            
    # Mostrar Guardia de Riesgo si hay datos del diario
    if psych_data:
        print("\n=========================================================")
        print("🛡️ ALERTA DEL GUARDIA DE RIESGO INSTITUCIONAL (IA MENTOR)")
        print("=========================================================")
        print(f"Hola, copiloto. Analicé tus {psych_data['total_sessions']} bitácoras. Tu balance neto acumulado es de: ${psych_data['total_pnl']:.2f} USD.")
        if len(psych_data["warnings"]) > 0:
            print("\n🚨 TUS ERRORES PSICOLÓGICOS MÁS RECURRENTES A EVITAR:")
            for warn in psych_data["warnings"][:2]:
                print(f" * {warn['error']}: presente en el {warn['percentage']}% de tus sesiones previas. ¡No caigas hoy en esto!")
        if len(psych_data["recent_lessons"]) > 0:
            print("\n📝 LECCIONES CLAVE DE TUS ÚLTIMAS SESIONES PARA REPASAR:")
            for les in psych_data["recent_lessons"][-3:]:
                print(f" * {les}")
        print("=========================================================")
        
    if ml_result:
        print("\n" + ml_result)

    # 11. Generar Visualización con Matplotlib
    fig, ax = plt.subplots(figsize=(15, 8))
    plt.style.use('dark_background')
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    # Velas
    for i in range(len(df)):
        open_p = df["open"].iloc[i]
        high_p = df["high"].iloc[i]
        low_p = df["low"].iloc[i]
        close_p = df["close"].iloc[i]
        
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
        ob_end = len(df) - 1
        ob_color = '#10b981' if row["OB"] == 1 else '#f43f5e'
        ob_label = 'OB Demanda Activo' if row["OB"] == 1 else 'OB Oferta Activo'
        
        rect = patches.Rectangle(
            (ob_start, row["Bottom"]),
            ob_end - ob_start,
            row["Top"] - row["Bottom"],
            facecolor=ob_color,
            edgecolor=ob_color,
            alpha=0.15,
            linestyle='--',
            linewidth=0.8,
            label=ob_label
        )
        ax.add_patch(rect)
        ax.hlines(row["Top"], ob_start, ob_end, colors=ob_color, linestyles='dashed', linewidth=0.5)
        ax.hlines(row["Bottom"], ob_start, ob_end, colors=ob_color, linestyles='dashed', linewidth=0.5)
        
    # FVGs
    for fvg in formatted_fvgs:
        fvg_color = '#06b6d4' if fvg["type"] == "Bullish" else '#eab308'
        rect = patches.Rectangle(
            (fvg["index"], fvg["bottom"]),
            len(df) - 1 - fvg["index"],
            fvg["top"] - fvg["bottom"],
            facecolor=fvg_color,
            edgecolor=fvg_color,
            alpha=0.08,
            linestyle=':',
            linewidth=0.5
        )
        ax.add_patch(rect)
        
    # BPRs
    for bpr in bprs:
        rect = patches.Rectangle(
            (min(bpr["bull_index"], bpr["bear_index"]), bpr["bottom"]),
            len(df) - 1 - min(bpr["bull_index"], bpr["bear_index"]),
            bpr["top"] - bpr["bottom"],
            facecolor='#a855f7',
            edgecolor='#a855f7',
            alpha=0.12,
            hatch='//',
            linewidth=0.6,
            label='BPR (Balanced Price Range)'
        )
        ax.add_patch(rect)

    # BOS y CHoCH
    for idx, row in recent_bos.iterrows():
        struct_color = '#38bdf8' if (row["BOS"] == 1 or row["CHOCH"] == 1) else '#f472b6'
        label_text = "BOS" if not pd.isna(row["BOS"]) else "CHoCH"
        direction = "▲" if (row["BOS"] == 1 or row["CHOCH"] == 1) else "▼"
        ax.hlines(row["Level"], idx, len(df)-1, colors=struct_color, linestyles='-.', linewidth=0.8)
        ax.text(idx, row["Level"], f" {label_text} {direction}", color=struct_color, fontsize=8, fontweight='bold', va='bottom')
        
    # Liquidez Externa
    if last_swing_high is not None:
        ax.hlines(last_swing_high['Level'], last_swing_high.name, len(df)-1, colors='#fb7185', linestyles='solid', linewidth=1.0)
        ax.text(last_swing_high.name, last_swing_high['Level'], " Liquidez Externa (High)", color='#fb7185', fontsize=8, fontweight='bold', va='bottom')
    if last_swing_low is not None:
        ax.hlines(last_swing_low['Level'], last_swing_low.name, len(df)-1, colors='#fb7185', linestyles='solid', linewidth=1.0)
        ax.text(last_swing_low.name, last_swing_low['Level'], " Liquidez Externa (Low)", color='#fb7185', fontsize=8, fontweight='bold', va='top')

    # Estilos
    ax.set_title(f"Escáner de Confluencias Pre-Trade - {symbol} ({resolution}m)", fontsize=16, color='#f8fafc', pad=15)
    ax.set_xlabel("Velas Recientes", color='#94a3b8')
    ax.set_ylabel("Precio", color='#94a3b8')
    ax.tick_params(colors='#94a3b8', labelsize=10)
    ax.grid(True, color='#334155', alpha=0.3, linestyle=':')
    
    for spine in ax.spines.values():
        spine.set_color('#1e293b')
        
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    if by_label:
        ax.legend(by_label.values(), by_label.keys(), loc='upper left', facecolor='#1e293b', edgecolor='#334155')

    # 12. Guardar reportes de forma dinámica y portátil (Neural Network Layout)
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    journal_dir = os.path.dirname(script_dir)
    bitacoras_dir = os.path.join(journal_dir, "bitacoras")
    imagenes_dir = os.path.join(journal_dir, "imagenes")
    
    os.makedirs(bitacoras_dir, exist_ok=True)
    os.makedirs(imagenes_dir, exist_ok=True)
    
    workspace_img_path = os.path.join(imagenes_dir, f"{today_str}_pre_trade.png")
    workspace_report_path = os.path.join(bitacoras_dir, f"{today_str}_pre_trade.md")
    
    # Rutas del directorio de artefactos activo de Gemini (espejo)
    artifact_dir = r"C:\Users\rsama\.gemini\antigravity-cli\brain\b648ecba-8292-44e4-b98d-350aa3c05f31"
    os.makedirs(artifact_dir, exist_ok=True)
    gemini_img_path = os.path.join(artifact_dir, "smc_analysis.png")
    gemini_report_path = os.path.join(artifact_dir, "smc_analysis_report.md")
    
    # Guardar gráficos
    plt.tight_layout()
    plt.savefig(workspace_img_path, dpi=150, facecolor='#0f172a')
    plt.savefig(gemini_img_path, dpi=150, facecolor='#0f172a')
    plt.close()
    
    # Escribir contenido markdown
    def write_report_content(f, img_link_src):
        f.write(f"""# 🛠️ Reporte Pre-Trade: Mapa de Confluencias (SMC & ICT)
        
Este reporte ha sido generado según los lineamientos de tu **Manual Operativo de Trading**. Analiza las confluencias de temporalidad menor para preparar tu Killzone y delinear tus puntos de interés antes de operar.

---

## 📅 Información de la Sesión
* **Fecha:** `{today_str}`
* **Activo:** `{symbol}`
* **Temporalidad:** `{resolution}m` (LTF / Gatillo)
* **Precio Actual:** `{last_price}`
* **Vinculación Temporal:** 
  * 🔗 [Ver Autopsia y Bitácora Post-Trade de esta Sesión]({today_str}_session.md) (Se generará al finalizar tu sesión)

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
            f.write("> [!NOTE]\n> Aún no se han detectado perfiles psicológicos previos. Asegúrate de registrar tus autopsias de sesión diarias en la carpeta `bitacoras/` para activar la retroalimentación de riesgo.\n")

        if ml_result:
            f.write(f"""
---

## 🧠 Predicción de Machine Learning (SMC Setup Classifier)
El clasificador de Inteligencia Artificial analizó la confluencia de este escenario de pre-sesión con tus datos históricos de trade:

```text
{ml_result}
```
""")

        f.write("""
---

## 🎨 Marcaciones Manuales en tu Gráfico (TradingView)
Esta sección extrae automáticamente tus rectángulos (cajas de zonas) y líneas dibujadas a mano en TradingView y comprueba su confluencia con las zonas de liquidez y estructuras de Smart Money Concepts:

""")
        if len(drawings_confluences) == 0:
            f.write("  * *No se detectaron marcaciones manuales activas en el gráfico (cajas grises o líneas de tendencia).* Asegúrate de marcar tus zonas en TradingView para integrarlas en el escáner.\n")
        else:
            for conf in drawings_confluences:
                f.write(f"{conf}\n")

        f.write("""
---

## ⏳ Análisis Estructural Multi-Temporalidad Completo (9 Timeframes)
Escaneo automático y en segundo plano de estructura de mercado y zonas institucionales activas en todos los marcos de tiempo analizados (de mayor a menor):

| Temporalidad | Sesgo Estructural | Rango (Premium/Discount) | Últimos OBs Activos | Últimos FVGs Activos |
| :--- | :--- | :--- | :--- | :--- |
""")
        for tf in ["4H", "1H", "30m", "15m", "5m", "4m", "3m", "2m", "1m"]:
            tf_data = all_tf_analysis[tf]
            bias = tf_data.get("bias", "Neutral")
            range_state = tf_data.get("range_state", "Desconocido")
            
            # Formatear OBs
            obs_list = []
            for ob in tf_data.get("obs", []):
                color = "🟢" if ob["type"] == "Demand" else "🔴"
                obs_list.append(f"{color} {ob['type']} ({ob['bottom']:.1f}-{ob['top']:.1f})")
            obs_str = ", ".join(obs_list) if obs_list else "*Ninguno*"
            
            # Formatear FVGs
            fvgs_list = []
            for fvg in tf_data.get("fvgs", []):
                color = "🟢" if fvg["type"] == "Bullish" else "🔴"
                fvgs_list.append(f"{color} {fvg['type']} ({fvg['bottom']:.1f}-{fvg['top']:.1f})")
            fvgs_str = ", ".join(fvgs_list) if fvgs_list else "*Ninguno*"
            
            f.write(f"| **{tf}** | {bias} | {range_state} | {obs_str} | {fvgs_str} |\n")

        f.write(f"""
---

## 📊 Mapa de Gráfico de Confluencias
Este gráfico mapea de forma precisa la liquidez externa, los bloques de orden activos, los vacíos de liquidez y los rangos de precio balanceados (BPR):

![Gráfico Pre-Trade]({img_link_src})

---

## 🔍 Análisis Estructural Top-Down (Multi-Temporalidad)
Análisis de temporalidades HTF de Nasdaq en el fondo sin alterar tu TradingView Desktop:

* **1H HTF Bias:** `{htf_analysis['1h']['bias']}` | Mapeado según el último BOS estructural en 1 hora.
* **1H Zonas Clave:**
""")
        if len(htf_analysis["1h"]["obs"]) == 0 and len(htf_analysis["1h"]["fvgs"]) == 0:
            f.write("  * *No se detectan OBs o FVGs de 1H inmitigados cercanos.*\n")
        else:
            for ob in htf_analysis["1h"]["obs"][:2]:
                f.write(f"  * OB de 1H {ob['type']}: Rango `{ob['bottom']:.2f} - {ob['top']:.2f}`\n")
            for fvg in htf_analysis["1h"]["fvgs"][:2]:
                f.write(f"  * FVG de 1H {fvg['type']}: Rango `{fvg['bottom']:.2f} - {fvg['top']:.2f}`\n")

        f.write(f"""
* **15m POIs de Confluencia:**
""")
        if len(htf_analysis["15m"]["obs"]) == 0 and len(htf_analysis["15m"]["fvgs"]) == 0:
            f.write("  * *No se detectan OBs o FVGs de 15m inmitigados cercanos.*\n")
        else:
            for ob in htf_analysis["15m"]["obs"][:2]:
                f.write(f"  * OB de 15m {ob['type']}: Rango `{ob['bottom']:.2f} - {ob['top']:.2f}` | Ver [[Order Block (Bullish)]] o [[Order Block (Bearish)]]\n")
            for fvg in htf_analysis["15m"]["fvgs"][:2]:
                f.write(f"  * FVG de 15m {fvg['type']}: Rango `{fvg['bottom']:.2f} - {fvg['top']:.2f}` | Ver [[Fair Value Gap]]\n")

        f.write(f"""
---

## ⚡ Correlación Inter-Mercado (SMT Divergence)
* **Estado SMT:** `{smt_result if smt_result else 'S&P 500 (MES) y Nasdaq (MNQ) alineados de forma regular en el Open (Sin divergencias activas). Ver [[SMT Divergence]]'}`

---

## 🧲 Puntos de Interés (POI) y Liquidez LTF ({resolution}m)

### 🌐 1. Liquidez Externa (HTF / Session Pivots)
Niveles clave para buscar barridas de liquidez (*sweeps*) en la apertura de sesión o Killzone:
""")
        if last_swing_high is not None:
            f.write(f"* **Liquidez Externa Superior (Swing High):** `{last_swing_high['Level']}` (Vela #{last_swing_high.name}) | Ver [[External Liquidity]] y [[Swing High]]\n")
        if last_swing_low is not None:
            f.write(f"* **Liquidez Externa Inferior (Swing Low):** `{last_swing_low['Level']}` (Vela #{last_swing_low.name}) | Ver [[External Liquidity]] y [[Swing Low]]\n")
            
        f.write("\n* **Pools de Liquidez Interna Activos (Unswept):**\n")
        if len(active_liquidity) == 0:
            f.write("  * *No se detectan pools de liquidez interna inmitigados en el rango de precios actual. Ver [[Internal Liquidity]]*\n")
        else:
            for idx, row in active_liquidity.iterrows():
                liq_dir = "Alcista (Highs) 🟢" if row["Liquidity"] == 1 else "Bajista (Lows) 🔴"
                f.write(f"  * Pool {liq_dir} en nivel `{row['Level']:.2f}` en la vela #{idx} | Ver [[Liquidity Sweep]]\n")
            
        f.write("""
### 🟢 2. Bloques de Orden de Demanda (Soportes / Compras)
Zonas institucionales activas de alta concentración de compras limitadas. Ver [[Order Block (Bullish)]].

| Tipo | Rango de Precio | Volumen | Estado |
| :--- | :--- | :--- | :--- |
""")
        for idx, row in active_obs[active_obs["OB"] == 1].iterrows():
            f.write(f"| **Demand OB** | `{row['Bottom']} - {row['Top']}` | `{row['OBVolume']}` | **Inmitigado (Activo)** 🔥 |\n")
            
        f.write("""
### 🔴 3. Bloques de Orden de Oferta (Resistencias / Ventas)
Zonas institucionales activas de alta concentración de ventas limitadas. Ver [[Order Block (Bearish)]].

| Tipo | Rango de Precio | Volumen | Estado |
| :--- | :--- | :--- | :--- |
""")
        for idx, row in active_obs[active_obs["OB"] == -1].iterrows():
            f.write(f"| **Supply OB** | `{row['Bottom']} - {row['Top']}` | `{row['OBVolume']}` | **Inmitigado (Activo)** ⚡ |\n")

        f.write("""
---

## 🌀 4. Anatomía de Fair Value Gaps (FVG) e Inversiones
Análisis detallado de imbalances de precios y su **probabilidad de inversión (iFVG)** según la secuencia de sus 3 velas. Ver [[Fair Value Gap]] e [[IFVG]].

| Dirección | Rango de FVG | Perfil de Velas | Probabilidad de Inversión / Comportamiento |
| :--- | :--- | :--- | :--- |
""")
        for fvg in formatted_fvgs:
            fvg_dir = "🟢 Bullish FVG" if fvg["type"] == "Bullish" else "🔴 Bearish FVG"
            fvg_range = f"{fvg['bottom']} - {fvg['top']}"
            fvg_profile = fvg['profile']
            fvg_prob = fvg['inversion_prob']
            fvg_idx = fvg['index']
            f.write(f"| {fvg_dir} | `{fvg_range}` | `{fvg_profile}` (Vela #{fvg_idx}) | {fvg_prob} |\n")

        f.write("""
---

## 🟣 5. Balanced Price Ranges (BPR) Detectados
Solapamientos de FVG alcistas y bajistas en el mismo nivel de precios. Actúan como soportes/resistencias magnéticos de altísima precisión. Ver [[Balanced Price Range]].
""")
        if len(bprs) == 0:
            f.write("* *No se detectan Balanced Price Ranges (BPR) solapados en las velas analizadas.*\n")
        else:
            for bpr in bprs:
                f.write(f"* **BPR Detectado:** Rango `{bpr['bottom']:.2f} - {bpr['top']:.2f}` | Solapamiento de FVG Alcista (Vela #{bpr['bull_index']}) y Bajista (Vela #{bpr['bear_index']})\n")

        f.write("""
---

## 🔄 6. Estructura de Mercado Reciente (BOS / CHoCH)
Rupturas de estructura registradas en el gráfico. Ver [[Market Structure]], [[Break of Structure]] y [[Change of Character]]:
""")
        for idx, row in recent_bos.iterrows():
            struct_name = "BOS (Break of Structure)" if not pd.isna(row["BOS"]) else "CHoCH (Change of Character)"
            direction = "Alcista 🟢" if (row["BOS"] == 1 or row["CHOCH"] == 1) else "Bajista 🔴"
            f.write(f"* **{struct_name} {direction}** en nivel `{row['Level']}` | Confirmado en la vela #{idx}\n")

        f.write(f"""
---

## 💡 Protocolo Operativo Pre-Trade (Tu Plan de Sesión)

> [!IMPORTANT]
> **Checklist antes de apretar el gatillo (LTF 1m - 5m):**
> 1. **Fase 1 (Sweep):** Espera a que el precio barra una de las zonas de **Liquidez Externa** (`{last_swing_high['Level'] if last_swing_high is not None else 'High'}` / `{last_swing_low['Level'] if last_swing_low is not None else 'Low'}`) o mitigue un POI HTF.
> 2. **Fase 2 (iFVG Trigger):** Busca una reacción post-sweep. El cuerpo de la vela debe cerrar y romper un FVG contrario, prioritariamente con perfil **Easy to Invert (R-G-R o G-R-G)**, convirtiéndolo en un **iFVG**.
> 3. **Gestión de Riesgo:** Si opera en All-Time Highs, gestión estricta con relación de **1:1 R:R**. En días de noticias, no ingresar a operaciones dentro de los **5 minutos anteriores** a la publicación.
""")

    # Guardar en local del usuario (relativo)
    with open(workspace_report_path, "w", encoding="utf-8") as f:
        write_report_content(f, f"../imagenes/{today_str}_pre_trade.png")

    # Guardar en Gemini (absoluto)
    with open(gemini_report_path, "w", encoding="utf-8") as f:
        write_report_content(f, f"file:///C:/Users/rsama/.gemini/antigravity-cli/brain/b648ecba-8292-44e4-b98d-350aa3c05f31/smc_analysis.png")

    print(f"¡Reporte Pre-Trade guardado con éxito en tu bitácora: {workspace_report_path}!")
    print(f"¡Reporte Espejo Gemini actualizado en: {gemini_report_path}!")

if __name__ == "__main__":
    main()
