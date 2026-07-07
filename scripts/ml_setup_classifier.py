#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import json
import math
import argparse
from pathlib import Path
from datetime import datetime as dt_class

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Imposibilitar caídas por falta de librerías al importar
try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import LeaveOneOut
except ImportError:
    print("Error: Faltan dependencias necesarias.")
    print("Por favor, ejecuta: pip install pandas scikit-learn numpy")
    sys.exit(1)

CONFLUENCE_MAPPING = {
    "htf-bias": "htf market structure bias confirmed",
    "bias": "htf market structure bias confirmed",
    "htf market structure bias confirmed": "htf market structure bias confirmed",
    
    "htf-zone": "in htf premium / discount zone",
    "zone": "in htf premium / discount zone",
    "discount": "in htf premium / discount zone",
    "premium": "in htf premium / discount zone",
    "in htf premium / discount zone": "in htf premium / discount zone",
    
    "htf-pd": "at htf pd array (ob / fvg / breaker)",
    "pd": "at htf pd array (ob / fvg / breaker)",
    "pd array": "at htf pd array (ob / fvg / breaker)",
    "at htf pd array (ob / fvg / breaker)": "at htf pd array (ob / fvg / breaker)",
    "bpr": "at htf pd array (ob / fvg / breaker)",
    "balanced price range": "at htf pd array (ob / fvg / breaker)",
    
    "fvg": "fair value gap (fvg) on entry tf",
    "fair value gap": "fair value gap (fvg) on entry tf",
    "fair value gap (fvg) on entry tf": "fair value gap (fvg) on entry tf",
    
    "ifvg": "inverse fvg / inverse structure present",
    "inverted fvg": "inverse fvg / inverse structure present",
    "inverse fvg": "inverse fvg / inverse structure present",
    "inverse fvg / inverse structure present": "inverse fvg / inverse structure present",
    
    "ob": "order block (ob) alignment",
    "order block": "order block (ob) alignment",
    "order block (ob) alignment": "order block (ob) alignment",
    
    "vi": "volume imbalance (vi) present",
    "volume imbalance": "volume imbalance (vi) present",
    "volume imbalance (vi) present": "volume imbalance (vi) present",
    
    "liq-swept": "buy-side / sell-side liquidity swept",
    "sweep": "buy-side / sell-side liquidity swept",
    "swept": "buy-side / sell-side liquidity swept",
    "liquidity sweep": "buy-side / sell-side liquidity swept",
    "buy-side / sell-side liquidity swept": "buy-side / sell-side liquidity swept",
    
    "eq-hl": "equal highs / lows tapped",
    "eq": "equal highs / lows tapped",
    "equal highs": "equal highs / lows tapped",
    "equal lows": "equal highs / lows tapped",
    "equal highs / lows tapped": "equal highs / lows tapped",
    
    "stop-hunt": "stop hunt / liquidity grab confirmed",
    "stop hunt": "stop hunt / liquidity grab confirmed",
    "liquidity grab": "stop hunt / liquidity grab confirmed",
    "stop hunt / liquidity grab confirmed": "stop hunt / liquidity grab confirmed",
    
    "bos": "bos confirmed on lower tf",
    "bos confirmed on lower tf": "bos confirmed on lower tf",
    
    "choch": "choch on entry tf",
    "choch on entry tf": "choch on entry tf",
    
    "smt": "smt divergence present",
    "smt divergence": "smt divergence present",
    "smt divergence present": "smt divergence present",
    
    "kz": "in kill zone (london / ny am / pm)",
    "kill zone": "in kill zone (london / ny am / pm)",
    "killzone": "in kill zone (london / ny am / pm)",
    "in kill zone (london / ny am / pm)": "in kill zone (london / ny am / pm)",
    
    "no-news": "no high-impact news in trade window",
    "news": "no high-impact news in trade window",
    "no news": "no high-impact news in trade window",
    "no high-impact news in trade window": "no high-impact news in trade window",
    
    "po3": "power of three phase aligned",
    "power of three": "power of three phase aligned",
    "power of three phase aligned": "power of three phase aligned",
    
    "stop-valid": "stop beyond swing low / high",
    "stop valid": "stop beyond swing low / high",
    "stop beyond swing low / high": "stop beyond swing low / high",
    
    "min-rr": "minimum 2r target available",
    "rr": "minimum 2r target available",
    "minimum 2r target available": "minimum 2r target available",
    
    "size": "position size within 1% risk",
    "position size": "position size within 1% risk",
    "position size within 1% risk": "position size within 1% risk"
}

def parse_confluences(conf_str):
    if not conf_str:
        return []
    parts = []
    for item in conf_str.replace(";", ",").replace("|", ",").split(","):
        stripped = item.strip().lower()
        if stripped:
            mapped = CONFLUENCE_MAPPING.get(stripped, stripped)
            parts.append(mapped)
    return parts

def safe_float(value, default=0.0):
    """Convierte un valor a float de forma segura, retornando un default si falla."""
    try:
        return float(str(value).strip()) if value else default
    except Exception:
        return default

def preprocess_data(entries):
    df_list = []
    unique_confluences = set()
    
    for e in entries:
        # Solo entrenar en trades completados (Win o Loss).
        # Los Breakeven (BE) se pueden catalogar como 0 (no ganados) o ignorar.
        # En este clasificador los trataremos como 0 (no ganados) para ser conservadores.
        result = e.get("result")
        if not result or result not in ["Win", "Loss", "BE"]:
            continue
            
        y = 1 if result == "Win" else 0
        
        confs = parse_confluences(e.get("confluences", ""))
        for c in confs:
            unique_confluences.add(c)
            
        # Parámetros básicos
        trade_data = {
            "id": e.get("id"),
            "instrument": e.get("instrument", "").strip().upper(),
            "direction": 1 if e.get("direction") == "Long" else 0,
            "session": e.get("session", "").strip(),
            "rr": float(e.get("rr") or 0.0),
            "confluences_raw": confs,
            "target": y
        }
        
        # --- Feature Engineering ---
        
        # FE1 - Hora del día (codificación cíclica basada en minutos desde apertura 08:00)
        dt_str = e.get("datetime", "")
        if len(dt_str) >= 16:
            try:
                hour = int(dt_str[11:13])
                minute = int(dt_str[14:16])
                mins_since_open = (hour - 8) * 60 + minute
                trade_data["hour_sin"] = math.sin(2 * math.pi * mins_since_open / 480)
                trade_data["hour_cos"] = math.cos(2 * math.pi * mins_since_open / 480)
            except (ValueError, IndexError):
                trade_data["hour_sin"] = 0.0
                trade_data["hour_cos"] = 1.0
        else:
            trade_data["hour_sin"] = 0.0
            trade_data["hour_cos"] = 1.0
        
        # FE3 - Conteo total de confluencias
        trade_data["n_confluences"] = len(confs)
        
        # FE4 - Ancho del Stop Loss (distancia entry-SL en puntos)
        trade_data["sl_width_pts"] = abs(safe_float(e.get("entry")) - safe_float(e.get("sl")))
        
        # FE5 - Día de la semana (0=Lunes ... 4=Viernes)
        if len(dt_str) >= 10:
            try:
                trade_data["day_of_week"] = dt_class.fromisoformat(dt_str[:10]).weekday()
            except (ValueError, TypeError):
                trade_data["day_of_week"] = 0
        else:
            trade_data["day_of_week"] = 0
        
        df_list.append(trade_data)
        
    if not df_list:
        return None, None
        
    df = pd.DataFrame(df_list)
    
    # One-hot encoding manual para confluencias específicas
    for c in sorted(unique_confluences):
        df[f"conf_{c}"] = df["confluences_raw"].apply(lambda x: 1 if c in x else 0)
        
    # One-hot encoding para Instrumentos y Sesiones
    df = pd.get_dummies(df, columns=["instrument", "session"], prefix=["inst", "sess"])
    
    # Limpiar columnas no necesarias para el entrenamiento
    df_features = df.drop(columns=["id", "confluences_raw", "target"])
    
    return df_features, df["target"]

def main():
    parser = argparse.ArgumentParser(description="Machine Learning setup classifier for your Trading Journal")
    parser.add_argument("--predict", action="store_true", help="Predice la probabilidad de éxito de un setup")
    parser.add_argument("--inst", type=str, default="NQ", help="Instrumento (ej. NQ, ES)")
    parser.add_argument("--dir", type=str, choices=["Long", "Short"], default="Long", help="Dirección (Long o Short)")
    parser.add_argument("--sess", type=str, default="NY AM KZ", help="Sesión (ej. NY AM KZ, London KZ)")
    parser.add_argument("--confs", type=str, default="", help="Lista de confluencias separadas por coma")
    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    journal_path = journal_dir / "journal.json"
    
    if not journal_path.exists():
        print(f"Error: No se encontró el archivo de diario en {journal_path}")
        print("Registra algunos trades en la UI primero.")
        return
        
    try:
        entries = json.loads(journal_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error leyendo {journal_path.name}: {e}")
        return
        
    # Filtrar entradas válidas
    valid_entries = [e for e in entries if e.get("result") in ["Win", "Loss", "BE"]]
    
    if len(valid_entries) < 6:
        print(f"Historial insuficiente: Tienes {len(valid_entries)} trades en tu diario.")
        print("El modelo requiere un mínimo de 6 trades registrados (Wins/Losses) para poder entrenarse.")
        return
        
    # Preprocesar
    X, y = preprocess_data(valid_entries)
    if X is None or len(X) == 0:
        print("No se encontraron características de confluencia consistentes.")
        return
        
    # Rellenar valores nulos con 0 por seguridad
    X = X.fillna(0)
    
    # Entrenar un clasificador Random Forest
    # Ajustado con pocos estimadores y profundidad baja para evitar sobreajuste en bases pequeñas
    clf = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
    clf.fit(X, y)
    
    if not args.predict:
        # === MODO DIAGNÓSTICO (PREDETERMINADO) ===
        print(f"=== MOTOR DE MACHINE LEARNING ENTRENADO ({len(X)} Trades) ===")
        
        # Calcular precisión del modelo (LOOCV para muestras pequeñas)
        if len(X) >= 10:
            loo = LeaveOneOut()
            scores = []
            for train_idx, test_idx in loo.split(X):
                X_tr, X_ts = X.iloc[train_idx], X.iloc[test_idx]
                y_tr, y_ts = y.iloc[train_idx], y.iloc[test_idx]
                temp_clf = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
                temp_clf.fit(X_tr, y_tr)
                scores.append(temp_clf.score(X_ts, y_ts))
            acc = np.mean(scores) * 100
            print(f"Precisión del Modelo (Cross-Val): {acc:.1f}%")
        else:
            acc = clf.score(X, y) * 100
            print(f"Precisión de Entrenamiento: {acc:.1f}% (Se requiere más historial para validación cruzada)")
            
        # Mostrar importancia de características (Feature Importance)
        importances = clf.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\n📊 PESO E IMPACTO DE TUS CONFLUENCIAS EN EL WIN RATE:")
        print("-" * 60)
        for i in range(min(12, len(X.columns))):
            col_name = X.columns[indices[i]]
            # Formatear el nombre para legibilidad
            clean_name = col_name.replace("conf_", "Tag: ").replace("inst_", "Instrumento: ").replace("sess_", "Sesión: ")
            val = importances[indices[i]] * 100
            bar = "█" * int(val / 3) if val > 0 else ""
            print(f"{clean_name:<30} | {val:>5.1f}% {bar}")
        print("-" * 60)
        print("Usa el parámetro '--predict' para evaluar un setup futuro en tiempo real.")
        print('Ejemplo: python scripts/ml_setup_classifier.py --predict --inst "NQ" --dir "Long" --sess "NY AM KZ" --confs "fvg, ob, smt"')
        
    else:
        # === MODO PREDICCIÓN EN VIVO ===
        print(f"=== PREDICCIÓN DE PROBABILIDAD DE ÉXITO ===")
        # Generar un vector de entrada idéntico al de entrenamiento
        input_data = {col: 0 for col in X.columns}
        
        # Llenar instrumento
        inst_col = f"inst_{args.inst.upper()}"
        if inst_col in input_data:
            input_data[inst_col] = 1
            
        # Llenar dirección
        if "direction" in input_data:
            input_data["direction"] = 1 if args.dir == "Long" else 0
            
        # Llenar sesión
        sess_col = f"sess_{args.sess}"
        if sess_col in input_data:
            input_data[sess_col] = 1
            
        # Llenar confluencias
        pred_confs = parse_confluences(args.confs)
        for c in pred_confs:
            conf_col = f"conf_{c}"
            if conf_col in input_data:
                input_data[conf_col] = 1
            else:
                # Si es una confluencia nueva no entrenada, avisar
                print(f"Nota: La confluencia '{c}' no existe en tu historial de entrenamiento. Se ignorará.")
                
        # Crear DataFrame para la predicción
        input_df = pd.DataFrame([input_data])
        
        # Predecir probabilidades
        probs = clf.predict_proba(input_df)[0]
        classes = list(clf.classes_)
        if 1 in classes:
            win_prob = probs[classes.index(1)] * 100
        else:
            win_prob = 0.0
            print("Advertencia: Historial insuficiente — todos los trades tienen el mismo resultado.")
        
        print("\n" + "=" * 50)
        print(f"SETUP EVALUADO:")
        print(f" - Instrumento: {args.inst.upper()} | Dirección: {args.dir} | Sesión: {args.sess}")
        print(f" - Confluencias: {', '.join(pred_confs)}")
        print("-" * 50)
        
        color_code = "\033[92m" if win_prob >= 65 else "\033[93m" if win_prob >= 45 else "\033[91m"
        reset_code = "\033[0m"
        
        # Verificar si la consola soporta colores ANSI (Windows a veces requiere activación, omitimos códigos si no)
        if os.name == 'nt':
            color_code, reset_code = "", ""
            
        print(f"PROBABILIDAD DE WIN RATE ESTIMADA: {color_code}{win_prob:.1f}%{reset_code}")
        
        if win_prob >= 65:
            print("🚀 SETUP ALTA PROBABILIDAD (A+): Recomendado operar con riesgo estándar (1.0%).")
        elif win_prob >= 45:
            print("⚠️ SETUP MODERADO: Reducir riesgo a la mitad (0.5%) o esperar más confirmaciones.")
        else:
            print("❌ SETUP BAJA PROBABILIDAD: Se sugiere estrictamente omitir el trade (No-Trade Zone).")
        print("=" * 50)

if __name__ == "__main__":
    main()
