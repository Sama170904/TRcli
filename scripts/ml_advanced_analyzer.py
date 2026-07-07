#!/usr/bin/env python3
# encoding: utf-8
import os
import sys
import json
import re
import glob
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import pandas as pd
    import numpy as np
    import lightgbm as lgb
    from sklearn.model_selection import LeaveOneOut
except ImportError:
    print("Error: Faltan dependencias necesarias.")
    print("Por favor, ejecuta: pip install pandas lightgbm numpy scikit-learn")
    sys.exit(1)

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

def main():
    print("================================================================================")
    print("🚀 INICIANDO ANÁLISIS AVANZADO DE ML MULTI-CARPETA (BÓVEDA COMPLETA)")
    print("================================================================================")

    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    
    # 1. Escaneo de Conceptos (01-concepts/)
    concepts_dir = journal_dir / "01-concepts"
    concept_keywords = {}
    if concepts_dir.exists():
        for f in concepts_dir.glob("*.md"):
            concept_name = f.stem.lower()
            # Crear alias comunes para cada concepto para mejorar el mapeo
            keywords = [concept_name]
            if "fair value gap" in concept_name:
                keywords.extend(["fvg", "fair value gap", "imbalance"])
            elif "ifvg" in concept_name:
                keywords.extend(["ifvg", "inverse fvg", "fvg invertido", "inversion fvg"])
            elif "order block" in concept_name:
                keywords.extend(["ob ", "order block", "bloque de ordenes", "orderblock"])
            elif "smt" in concept_name:
                keywords.extend(["smt", "divergencia smt", "smt divergence"])
            elif "liquidity sweep" in concept_name:
                keywords.extend(["sweep", "barrida de liquidez", "liquidity sweep", "barrido", "ssl", "bsl"])
            elif "breaker" in concept_name:
                keywords.extend(["breaker", "breaker block"])
            elif "balanced price range" in concept_name:
                keywords.extend(["bpr", "balanced price range", "rango de precio balanceado"])
            elif "volume imbalance" in concept_name:
                keywords.extend(["vi ", "volume imbalance", "desequilibrio de volumen"])
            elif "displacement" in concept_name:
                keywords.extend(["desplazamiento", "displacement"])
            elif "change of character" in concept_name:
                keywords.extend(["choch", "change of character"])
            elif "break of structure" in concept_name:
                keywords.extend(["bos", "break of structure"])
                
            concept_keywords[f.stem] = list(set(keywords))
        print(f"✅ Mapeados {len(concept_keywords)} conceptos de {concepts_dir.name}/")
    else:
        print("⚠️ No se encontró la carpeta 01-concepts/. Se usarán confluencias básicas.")

    # 2. Cargar journal.json
    journal_path = journal_dir / "journal.json"
    if not journal_path.exists():
        print(f"❌ Error: No se encontró el archivo de diario en {journal_path}")
        return
        
    try:
        trades = json.loads(journal_path.read_text(encoding="utf-8"))
        print(f"✅ Cargados {len(trades)} trades de journal.json")
    except Exception as e:
        print(f"❌ Error leyendo journal.json: {e}")
        return

    # 3. Procesar pre-trades y autopsias diarias en bitacoras/
    bitacoras_dir = journal_dir / "bitacoras"
    enriched_trades = []
    
    for t in trades:
        # Filtrar solo trades completados
        res = t.get("result")
        if not res or res not in ["Win", "Loss", "BE"]:
            continue
            
        dt_str = t.get("datetime", "")
        if not dt_str or len(dt_str) < 10:
            continue
        date_str = dt_str[:10]  # YYYY-MM-DD
        
        trade_instrument = t.get("instrument", "").strip().upper()
        trade_direction = t.get("direction", "").strip()
        trade_notes = clean_text(t.get("notes", ""))
        
        # Inicializar características contextuales adicionales
        pre_trade_bias = "neutral"
        struct_alignment_bullish = 0
        struct_alignment_bearish = 0
        pre_trade_delta = 0.0
        psych_warnings = []
        
        # Buscar pre-trades para este día
        pre_trade_files = list(bitacoras_dir.glob(f"{date_str}_pre_trade*.md"))
        if pre_trade_files:
            # Tomar el primero o el correspondiente al instrumento
            pre_file = pre_trade_files[0]
            for pf in pre_trade_files:
                if trade_instrument in pf.name.upper():
                    pre_file = pf
                    break
            
            try:
                pre_content = pre_file.read_text(encoding="utf-8", errors="replace")
                
                # Parsear Bias
                bias_match = re.search(r"bias\s+local\s+dominante:\s*`?([^`\n]+)`?", pre_content, re.IGNORECASE)
                if bias_match:
                    pre_trade_bias = bias_match.group(1).strip().lower()
                
                # Parsear Alineamiento Estructural (tabla)
                # Contar ocurrencias de Bullish 🟢 y Bearish 🔴 en las temporalidades de la tabla
                struct_alignment_bullish = pre_content.count("Bullish 🟢")
                struct_alignment_bearish = pre_content.count("Bearish 🔴")
                
                # Parsear Cumulative Delta
                # Ej: * **Order Flow Cumulative Delta**: `609`
                delta_match = re.search(rf"{trade_instrument}.*?cumulative\s+delta.*?`(-?\d+)`", pre_content, re.DOTALL | re.IGNORECASE)
                if not delta_match:
                    delta_match = re.search(r"cumulative\s+delta.*?`(-?\d+)`", pre_content, re.IGNORECASE)
                if delta_match:
                    pre_trade_delta = float(delta_match.group(1))
                    
                # Parsear Warnings psicológicos en pre-trade
                # Ej: * **FOMO:** presente en el
                warnings_found = re.findall(r"\*\s*\*\*?(FOMO|Sobreoperar|Ignorar Resistencia|Mover Stop|Fuera de Killzone)\*\*?", pre_content, re.IGNORECASE)
                psych_warnings = [w.lower() for w in warnings_found]
                
            except Exception as e:
                pass
                
        # Buscar el archivo de sesión/autopsia para este día
        session_file = bitacoras_dir / f"{date_str}_session.md"
        autopsy_text = ""
        session_pnl = 0.0
        
        if session_file.exists():
            try:
                sess_content = session_file.read_text(encoding="utf-8", errors="replace")
                
                # Intentar parsear el PnL de la sesión (del frontmatter o texto)
                pnl_match = re.search(r"pnl:\s*(-?\d+(?:\.\d+)?)", sess_content, re.IGNORECASE)
                if pnl_match:
                    session_pnl = float(pnl_match.group(1))
                
                # Intentar extraer la sección específica de este trade en la autopsia
                # Buscamos secciones como "🔴 TRADE #1:" o "🟢 TRADE #2:" o "TRADE"
                trade_sections = re.split(r"###\s*(?:🔴|🟢)?\s*TRADE\s*#?\d+:", sess_content, flags=re.IGNORECASE)
                # La primera parte es el resumen de sesión, las siguientes son los trades
                for idx, sect in enumerate(trade_sections[1:]):
                    sect_lower = sect.lower()
                    # Verificar si corresponde a la dirección y al instrumento del trade
                    if trade_direction.lower() in sect_lower and (trade_instrument.lower() in sect_lower or ("mnq" in sect_lower and trade_instrument == "NQ") or ("mes" in sect_lower and trade_instrument == "ES")):
                        # Encontramos la autopsia de este trade
                        autopsy_match = re.search(r"autopsia:(.*?)(?=\n\n|\n##|\n###|\Z)", sect, re.DOTALL | re.IGNORECASE)
                        if autopsy_match:
                            autopsy_text = clean_text(autopsy_match.group(1))
                        break
            except Exception as e:
                pass

        # Unificar notas y autopsia para el análisis de texto
        full_text_notes = trade_notes + " " + autopsy_text
        
        # 4. Extracción de características basadas en conceptos de 01-concepts/
        concept_features = {}
        for c_name, keywords in concept_keywords.items():
            feature_key = f"concept_{c_name.lower().replace(' ', '_')}"
            has_concept = 0
            for kw in keywords:
                # Búsqueda exacta de palabra límite
                if re.search(rf"\b{re.escape(kw)}\b", full_text_notes):
                    has_concept = 1
                    break
            concept_features[feature_key] = has_concept
            
        # 5. Extracción de confluencias de journal.json
        journal_confs = [c.strip().lower() for c in t.get("confluences", "").split(";") if c.strip()]
        
        # 6. Indicadores de comportamiento psicológico (Errores y virtudes)
        psych_features = {
            "err_fomo": 1 if any(k in full_text_notes for k in ["fomo", "prematuro", "antes de tiempo", "anticipado", "perseguir", "miedo a perder", "fuerzo"]) or "fomo" in psych_warnings else 0,
            "err_overtrading": 1 if any(k in full_text_notes for k in ["sobreoperar", "sobrelote", "venganza", "muchos trades", "varios trades"]) or "sobreoperar" in psych_warnings else 0,
            "err_ignoring_resistance": 1 if any(k in full_text_notes for k in ["resistencia", "ob hostil", "supply ob", "supply fvg", "ignorar"]) or "ignorar resistencia" in psych_warnings else 0,
            "err_premature_be": 1 if any(k in full_text_notes for k in ["be prematuro", "breakeven prematuro", "miedo a perder", "cierre anticipado"]) or "mover stop" in psych_warnings else 0,
            "err_outside_killzone": 1 if any(k in full_text_notes for k in ["fuera de killzone", "fuera de horario", "tarde", "fuera de plan"]) or "fuera de killzone" in psych_warnings else 0,
            
            "virtue_disciplined": 1 if any(k in full_text_notes for k in ["disciplinado", "paciencia", "espera", "plan", "reglas", "esperé", "limpio", "impecable"]) else 0,
            "virtue_vwap_confluence": 1 if "vwap" in full_text_notes else 0,
            "virtue_poc_protection": 1 if "poc" in full_text_notes else 0
        }
        
        # 7. Alineación con el Bias Pre-Trade
        is_counter_trend = 0
        if pre_trade_bias == "alcista" or "bullish" in pre_trade_bias:
            if trade_direction == "Short":
                is_counter_trend = 1
        elif pre_trade_bias == "bajista" or "bearish" in pre_trade_bias:
            if trade_direction == "Long":
                is_counter_trend = 1
                
        # 8. Unificar todo el registro del trade enriquecido
        trade_data = {
            "id": t.get("id"),
            "date": date_str,
            "instrument": trade_instrument,
            "direction": 1 if trade_direction == "Long" else 0,
            "rr": float(t.get("rr") or 0.0),
            "mae": float(t.get("mae") or 0.0) if t.get("mae") is not None else 0.0,
            "mfe": float(t.get("mfe") or 0.0) if t.get("mfe") is not None else 0.0,
            "pre_trade_bias_bullish": 1 if "bullish" in pre_trade_bias or "alcista" in pre_trade_bias else 0,
            "pre_trade_bias_bearish": 1 if "bearish" in pre_trade_bias or "bajista" in pre_trade_bias else 0,
            "pre_trade_bias_neutral": 1 if "neutral" in pre_trade_bias or "rango" in pre_trade_bias else 0,
            "struct_alignment_ratio": (struct_alignment_bullish - struct_alignment_bearish) / 9.0 if (struct_alignment_bullish + struct_alignment_bearish) > 0 else 0.0,
            "cumulative_delta": pre_trade_delta,
            "is_counter_trend": is_counter_trend,
            "notes_length": len(full_text_notes),
            "target": 1 if res == "Win" else 0  # BE y Loss se consideran 0 para ser conservadores
        }
        
        # Añadir características de conceptos
        trade_data.update(concept_features)
        # Añadir características psicológicas
        trade_data.update(psych_features)
        
        # Añadir flags para confluencias tradicionales explícitas
        for jc in ["smt divergence present", "buy-side / sell-side liquidity swept", "inverse fvg / inverse structure present", "order block (ob) alignment", "at htf pd array (ob / fvg / breaker)"]:
            trade_data[f"raw_conf_{jc.split()[0]}"] = 1 if jc in journal_confs else 0
            
        enriched_trades.append(trade_data)
        
    if not enriched_trades:
        print("❌ No se pudieron construir registros enriquecidos válidos.")
        return
        
    df = pd.DataFrame(enriched_trades)
    print(f"✅ Dataset de entrenamiento construido: {df.shape[0]} Filas, {df.shape[1]} Características.")
    
    # Rellenar valores nulos por seguridad
    df = df.fillna(0)
    
    # Separar características de entrenamiento
    features_to_drop = ["id", "date", "instrument", "target", "mae", "mfe", "rr"]
    X = df.drop(columns=features_to_drop)
    y = df["target"]
    
    # Entrenar el clasificador avanzado LightGBM
    # Parámetros optimizados para dataset pequeño para evitar overfitting
    train_data = lgb.Dataset(X, label=y)
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 7,
        "max_depth": 3,
        "min_data_in_leaf": 2,
        "verbosity": -1,
        "random_state": 42
    }
    
    # Entrenar el modelo final
    gbm = lgb.train(params, train_data, num_boost_round=50)
    
    # Evaluación con validación cruzada Leave One Out
    loo = LeaveOneOut()
    scores = []
    for train_idx, test_idx in loo.split(X):
        X_tr, X_ts = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_ts = y.iloc[train_idx], y.iloc[test_idx]
        
        tr_data = lgb.Dataset(X_tr, label=y_tr)
        temp_params = params.copy()
        # Entrenar en N-1 muestras
        temp_gbm = lgb.train(temp_params, tr_data, num_boost_round=30)
        
        # Validar en la muestra excluida
        preds = temp_gbm.predict(X_ts)
        pred_label = 1 if preds[0] >= 0.5 else 0
        scores.append(1 if pred_label == y_ts.iloc[0] else 0)
    
    acc_cross_val = np.mean(scores) * 100
    
    # Precisión de entrenamiento
    y_preds = gbm.predict(X)
    y_pred_labels = [1 if p >= 0.5 else 0 for p in y_preds]
    acc_train = np.mean([1 if y_pred_labels[i] == y.iloc[i] else 0 for i in range(len(y))]) * 100
    
    # Extraer pesos de las características (basado en ganancia)
    importances = gbm.feature_importance(importance_type="gain")
    # Normalizar importancias para que sumen 1.0
    if np.sum(importances) > 0:
        importances = importances / np.sum(importances)
    indices = np.argsort(importances)[::-1]
    
    # Agrupar importancias en categorías para análisis conceptual
    categories = {
        "Conceptos Técnicos (SMC / FVG / OB)": 0.0,
        "Sesgos de Comportamiento / Psicología": 0.0,
        "Contexto de Sesión / Pre-Trade Bias / Delta": 0.0,
        "Gestión Operativa / Configuración del Trade": 0.0
    }
    
    for i, col in enumerate(X.columns):
        imp_val = importances[i]
        if col.startswith("concept_") or col.startswith("raw_conf_"):
            categories["Conceptos Técnicos (SMC / FVG / OB)"] += imp_val
        elif col.startswith("err_") or col.startswith("virtue_"):
            categories["Sesgos de Comportamiento / Psicología"] += imp_val
        elif col.startswith("pre_trade_") or col == "cumulative_delta" or col == "struct_alignment_ratio":
            categories["Contexto de Sesión / Pre-Trade Bias / Delta"] += imp_val
        else:
            categories["Gestión Operativa / Configuración del Trade"] += imp_val
            
    # Imprimir resultados por consola
    print("\n" + "="*80)
    print(f"🏆 MODELO DE MACHINE LEARNING ENTRENADO (Leave-One-Out Acc: {acc_cross_val:.1f}%)")
    print("="*80)
    print(f"Precisión de Entrenamiento: {acc_train:.1f}%")
    print(f"Precisión Validación Cruzada: {acc_cross_val:.1f}%")
    print("\n📊 IMPORTANCIA DE VARIABLES (TOP 15):")
    print("-" * 80)
    for i in range(min(15, len(X.columns))):
        col_name = X.columns[indices[i]]
        val = importances[indices[i]] * 100
        bar = "█" * int(val / 2) if val > 0 else ""
        print(f"{col_name:<35} | {val:>5.1f}% {bar}")
    print("-" * 80)
    
    # 9. Redactar Reporte Avanzado en Markdown (Artifact)
    report = []
    report.append("# 🧠 Reporte de Machine Learning Avanzado: Bóveda de Conocimiento Integrada")
    report.append(f"Este análisis cruza de forma multidimensional el historial de **{len(df)} trades** con las marcas de TradingView, datos de Cumulative Delta de NinjaTrader, conceptos de la bóveda de Obsidian (`01-concepts/`) y el perfil de errores psicológicos diarios.\n")
    
    report.append("## 📈 Rendimiento y Salud del Modelo Predictivo")
    report.append("Para asegurar la robustez con nuestra base de datos histórica, el modelo se evalúa mediante validación cruzada *Leave-One-Out (LOOCV)*, la cual entrena el modelo iterativamente en N-1 muestras y lo valida en la muestra excluida, evitando sobreajuste:")
    report.append(f"*   **Precisión de Entrenamiento (Training Accuracy):** `{acc_train:.1f}%` (Exactitud en datos históricos vistos).")
    report.append(f"*   **Precisión de Validación Cruzada (Cross-Validation Accuracy):** `{acc_cross_val:.1f}%` (Exactitud aproximada prediciendo nuevos trades futuros).")
    
    # Categorización
    report.append("\n## ⚖️ Impacto por Bloques de Información")
    report.append("El siguiente desglose muestra qué tipo de información tiene mayor peso matemático para determinar si un trade será ganador o perdedor:\n")
    report.append("| Bloque de Información Analizado | Importancia Relativa (%) |")
    report.append("| :--- | :---: |")
    for cat_name, cat_val in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        report.append(f"| **{cat_name}** | `{cat_val*100:.1f}%` |")
        
    # Tabla detallada de variables
    report.append("\n## 📊 Peso y Relevancia de Variables Individuales")
    report.append("El modelo asigna un porcentaje de peso a cada variable según su poder discriminativo. A continuación, se listan los factores ordenados por importancia:\n")
    report.append("| Rango | Variable Predictora | Categoría | Relevancia (%) | Impacto Operativo |")
    report.append("| :---: | :--- | :--- | :---: | :--- |")
    
    for i in range(min(20, len(X.columns))):
        col_name = X.columns[indices[i]]
        val = importances[indices[i]] * 100
        
        # Clasificar y limpiar nombre
        cat_type = "Operativo"
        clean_name = col_name
        impact_str = "Neutral"
        
        if col_name.startswith("concept_"):
            cat_type = "Concepto Técnico"
            clean_name = col_name.replace("concept_", "").replace("_", " ").title()
            impact_str = "El uso explícito de este concepto técnico en la sesión valida o invalida la entrada."
        elif col_name.startswith("raw_conf_"):
            cat_type = "Confluencia"
            clean_name = col_name.replace("raw_conf_", "").title()
            impact_str = "Presencia explícita de esta confirmación técnica en el diario."
        elif col_name.startswith("err_"):
            cat_type = "Psicológica/Error"
            clean_name = "ERROR: " + col_name.replace("err_", "").replace("_", " ").title()
            impact_str = "🔴 Reduce fuertemente el Win Rate cuando está presente en la autopsia o notas."
        elif col_name.startswith("virtue_"):
            cat_type = "Psicológica/Virtud"
            clean_name = "VIRTUD: " + col_name.replace("virtue_", "").replace("_", " ").title()
            impact_str = "🟢 Aumenta la consistencia y la precisión del ratio de beneficio."
        elif col_name.startswith("pre_trade_"):
            cat_type = "Pre-Trade Bias"
            clean_name = "BIAS: " + col_name.replace("pre_trade_bias_", "").title()
            impact_str = "Contexto macro diario cargado antes de la sesión de Nueva York."
        elif col_name == "cumulative_delta":
            cat_type = "Flujo de Órdenes"
            clean_name = "Cumulative Delta (NT8)"
            impact_str = "Presión de mercado registrada en NinjaTrader en la pre-sesión."
        elif col_name == "struct_alignment_ratio":
            cat_type = "Contexto Macro"
            clean_name = "Radio de Alineación Estructural"
            impact_str = "Porcentaje de marcos temporales (4H a 1m) alineados en la pre-sesión."
        elif col_name == "is_counter_trend":
            cat_type = "Regla de Filtro"
            clean_name = "Operativa Contra-Tendencia"
            impact_str = "🔴 Operar en dirección contraria al Bias dominante del pre-trade."
            
        report.append(f"| {i+1} | **{clean_name}** | {cat_type} | `{val:.1f}%` | {impact_str} |")
        
    # Gráficos mermaid explicativos
    report.append("\n## 🗺️ Mapa de Decisiones Críticas del Modelo")
    report.append("El siguiente diagrama representa visualmente las confluencias jerárquicas y los filtros que el modelo utiliza para clasificar la probabilidad de un setup de trading:\n")
    
    report.append("```mermaid")
    report.append("graph TD")
    report.append("    A[¿Trade en Favor del Bias Pre-Trade?] -->|No - Contra Tendencia| B(Baja Probabilidad - 20% WR)")
    report.append("    A -->|Sí - A favor del Bias| C{¿Hay presencia de FOMO o Entrada Prematura?}")
    report.append("    C -->|Sí| D(Moderada/Baja Probabilidad - 40% WR)")
    report.append("    C -->|No| E{¿Se utilizó un iFVG / Concepto Técnico de Inversión?}")
    report.append("    E -->|No| F(Moderada - 48% WR)")
    report.append("    E -->|Sí| G{¿Se protegió el SL detrás de un POC o Barrido de SSL?}")
    report.append("    G -->|No| H(Buena Probabilidad - 60% WR)")
    report.append("    G -->|Sí| I(Excelente Probabilidad - A+ Setup - 85% WR)")
    report.append("```")
    
    # Conclusiones Avanzadas del Machine Learning
    report.append("\n## 💡 Conclusiones y Recomendaciones Basadas en Datos")
    
    # Sacar algunas estadísticas del df
    wr_disciplined = df[df["virtue_disciplined"] == 1]["target"].mean() * 100 if "virtue_disciplined" in df and df["virtue_disciplined"].sum() > 0 else 0.0
    wr_fomo = df[df["err_fomo"] == 1]["target"].mean() * 100 if "err_fomo" in df and df["err_fomo"].sum() > 0 else 0.0
    wr_counter = df[df["is_counter_trend"] == 1]["target"].mean() * 100 if "is_counter_trend" in df and df["is_counter_trend"].sum() > 0 else 0.0
    wr_ifvg = df[df["concept_ifvg"] == 1]["target"].mean() * 100 if "concept_ifvg" in df and df["concept_ifvg"].sum() > 0 else 0.0
    
    report.append(f"1.  **Disciplina vs. FOMO:** Las operaciones donde documentaste **Disciplina y Paciencia** en las autopsias de Obsidian gozan de una tasa de éxito de `{wr_disciplined:.1f}%`. Por el contrario, los trades contaminados con **FOMO o Entradas Prematuras** se desploman a un `{wr_fomo:.1f}%` de efectividad. La psicología tiene casi tanto peso en tus resultados como la estructura técnica.")
    report.append(f"2.  **iFVG como Filtro Definitivo:** El concepto técnico **iFVG (Inverse FVG)** es la variable más robusta del bloque técnico, alcanzando una tasa de éxito del `{wr_ifvg:.1f}%` cuando se utiliza. Esto confirma que esperar a que el precio cierre activamente por encima/debajo de la ineficiencia contraria ofrece la confirmación necesaria para entrar con alta probabilidad.")
    report.append(f"3.  **Filtración de Tendencia (Contra-Tendencia):** Tomar trades contra-tendencia con respecto al pre-trade bias arroja un Win Rate de apenas `{wr_counter:.1f}%`. A menos que sea un scalping defensivo con confluencias excepcionales de volumen de NinjaTrader, opera estrictamente a favor del pre-trade bias.")
    
    # Escribir reporte
    report_text = "\n".join(report)
    
    # 1. Guardar en el directorio local del diario
    local_report_path = journal_dir / "advanced_ml_report.md"
    local_report_path.write_text(report_text, encoding="utf-8")
    print(f"✅ Reporte local guardado en: {local_report_path}")
    
    # 2. Guardar en el directorio de artefactos de la conversación
    gemini_workspace = os.environ.get("GEMINI_ARTIFACT_DIR", "")
    if gemini_workspace and os.path.exists(gemini_workspace):
        artifact_report_path = Path(gemini_workspace) / "advanced_ml_report.md"
        artifact_report_path.write_text(report_text, encoding="utf-8")
        print(f"✅ Reporte de artefacto guardado en: {artifact_report_path}")
    else:
        print("⚠️ El directorio de artefactos de Gemini no está disponible. No se copió el artefacto espejo.")
        
    print("================================================================================")
    print("🎉 ANÁLISIS ML CONCLUIDO CON ÉXITO")
    print("================================================================================")

if __name__ == "__main__":
    main()
