import os
import json
import re
from pathlib import Path

def parse_confluences(conf_str):
    if not conf_str:
        return []
    # Separar por punto y coma, eliminar espacios vacíos
    parts = [p.strip().lower() for p in conf_str.split(";") if p.strip()]
    # Normalizar algunas confluencias similares
    normalized = []
    for p in parts:
        if "smt" in p:
            normalized.append("smt divergence")
        elif "liquidity swept" in p or "liquidity sweep" in p or "sweep" in p:
            normalized.append("liquidity swept")
        elif "stop hunt" in p or "liquidity grab" in p:
            normalized.append("stop hunt / liquidity sweep")
        elif "htf market structure bias" in p or "bias confirmed" in p:
            normalized.append("htf bias alignment")
        elif "inverse fvg" in p or "inverse structure" in p or "ifvg" in p:
            normalized.append("inverse fvg (ifvg)")
        elif "order block" in p or "ob alignment" in p:
            normalized.append("order block alignment")
        elif "htf pd array" in p or "pd array" in p:
            normalized.append("htf pd array mitigation")
        elif "kill zone" in p or "killzone" in p:
            normalized.append("kill zone timing")
        elif "premium" in p or "discount" in p:
            normalized.append("htf premium/discount zone")
        elif "bos" in p:
            normalized.append("bos confirmation")
        elif "choch" in p:
            normalized.append("choch confirmation")
        else:
            normalized.append(p)
    return list(set(normalized))

def analyze_patterns():
    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    journal_path = journal_dir / "journal.json"
    
    if not journal_path.exists():
        print(f"Error: No se encontró el archivo de diario en {journal_path}")
        return
        
    try:
        with open(journal_path, "r", encoding="utf-8") as f:
            trades = json.load(f)
    except Exception as e:
        print(f"Error leyendo journal.json: {e}")
        return
        
    total_trades = len(trades)
    if total_trades == 0:
        print("El diario está vacío. Registra trades para buscar patrones.")
        return
        
    wins = [t for t in trades if t.get("result") == "Win"]
    losses = [t for t in trades if t.get("result") == "Loss"]
    bes = [t for t in trades if t.get("result") == "BE"]
    
    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(bes)
    
    # Win rate clásico: Wins / (Wins + Losses)
    valid_decisions = win_count + loss_count
    win_rate = (win_count / valid_decisions * 100) if valid_decisions > 0 else 0.0
    
    print(f"Analizando {total_trades} trades históricos...")
    print(f"Wins: {win_count} | Losses: {loss_count} | BEs: {be_count}")
    print(f"Win Rate Efectivo: {win_rate:.1f}%\n")
    
    # 1. Frecuencia y efectividad de confluencias individuales
    confluence_stats = {}
    
    for t in trades:
        result = t.get("result")
        confs = parse_confluences(t.get("confluences", ""))
        notes = t.get("notes", "").lower()
        
        # Buscar palabras clave en las notas para confluencias implícitas (ej: absorción u SMT si no están explícitas)
        if "smt" in notes and "smt divergence" not in confs:
            confs.append("smt divergence")
        if ("absorcion" in notes or "absorción" in notes or "absorbed" in notes or "absorb" in notes) and "orderflow absorption" not in confs:
            confs.append("orderflow absorption")
            
        t["parsed_confs"] = confs # Almacenar para análisis cruzado
        
        for c in confs:
            if c not in confluence_stats:
                confluence_stats[c] = {"total": 0, "wins": 0, "losses": 0, "bes": 0}
            confluence_stats[c]["total"] += 1
            if result == "Win":
                confluence_stats[c]["wins"] += 1
            elif result == "Loss":
                confluence_stats[c]["losses"] += 1
            elif result == "BE":
                confluence_stats[c]["bes"] += 1
                
    # 2. Análisis del impacto de la ABSENCIA de confluencias clave
    # Analizamos qué pasa si no se tiene SMT, Absorción, Bias HTF, etc.
    key_conditions = ["smt divergence", "orderflow absorption", "htf bias alignment", "liquidity swept", "htf pd array mitigation", "inverse fvg (ifvg)"]
    absence_stats = {}
    
    for cond in key_conditions:
        absence_stats[cond] = {"total_without": 0, "wins_without": 0, "losses_without": 0, "bes_without": 0}
        for t in trades:
            result = t.get("result")
            confs = t["parsed_confs"]
            if cond not in confs:
                absence_stats[cond]["total_without"] += 1
                if result == "Win":
                    absence_stats[cond]["wins_without"] += 1
                elif result == "Loss":
                    absence_stats[cond]["losses_without"] += 1
                elif result == "BE":
                    absence_stats[cond]["bes_without"] += 1
                    
    # 3. Análisis de MAE / MFE por resultado
    mae_wins, mfe_wins = [], []
    mae_losses, mfe_losses = [], []
    
    for t in trades:
        res = t.get("result")
        mae = t.get("mae")
        mfe = t.get("mfe")
        
        if mae is not None and mfe is not None:
            try:
                mae_val = float(mae)
                mfe_val = float(mfe)
                if res == "Win":
                    mae_wins.append(mae_val)
                    mfe_wins.append(mfe_val)
                elif res == "Loss":
                    mae_losses.append(mae_val)
                    mfe_losses.append(mfe_val)
            except ValueError:
                pass
                
    avg_mae_win = sum(mae_wins) / len(mae_wins) if mae_wins else 0.0
    avg_mfe_win = sum(mfe_wins) / len(mfe_wins) if mfe_wins else 0.0
    avg_mae_loss = sum(mae_losses) / len(mae_losses) if mae_losses else 0.0
    avg_mfe_loss = sum(mfe_losses) / len(mfe_losses) if mfe_losses else 0.0

    # 4. Análisis por Instrumento (ES vs NQ)
    instrument_stats = {}
    for t in trades:
        inst = t.get("instrument", "Desconocido").upper()
        res = t.get("result")
        
        if inst not in instrument_stats:
            instrument_stats[inst] = {"total": 0, "wins": 0, "losses": 0, "bes": 0, "rr_sum": 0.0, "rr_count": 0}
            
        instrument_stats[inst]["total"] += 1
        
        try:
            rr = float(t.get("rr", 0.0))
            if rr > 0:
                instrument_stats[inst]["rr_sum"] += rr
                instrument_stats[inst]["rr_count"] += 1
        except ValueError:
            pass
            
        if res == "Win":
            instrument_stats[inst]["wins"] += 1
        elif res == "Loss":
            instrument_stats[inst]["losses"] += 1
        elif res == "BE":
            instrument_stats[inst]["bes"] += 1

    # 5. Análisis de patrones conductuales en las notas (Errores)
    behavioral_keywords = {
        "fomo / entrada prematura": ["fomo", "prematura", "antes de tiempo", "perder el movimiento", "persiguiendo"],
        "sobreloteo / riesgo excesivo": ["sobrelote", "sobreloteo", "lotes de más", "riesgo excesivo", "loteado"],
        "duda / ejecución tardía": ["duda", "tarde", "ejecucion tardia", "miedo", "vacilar"],
        "indisciplina / fuera de plan": ["fuera de plan", "fuera de reglas", "improvisar", "emocional", "venganza"],
        "be prematuro / miedo a perder": ["be prematuro", "miedo a perder", "cierre anticipado", "muevo a be"]
    }
    
    behavioral_stats = {k: {"total": 0, "wins": 0, "losses": 0} for k in behavioral_keywords.keys()}
    for t in trades:
        notes = t.get("notes", "").lower()
        res = t.get("result")
        for pattern, keywords in behavioral_keywords.items():
            for kw in keywords:
                if kw in notes:
                    behavioral_stats[pattern]["total"] += 1
                    if res == "Win":
                        behavioral_stats[pattern]["wins"] += 1
                    elif res == "Loss":
                        behavioral_stats[pattern]["losses"] += 1
                    break

    # Escribir reporte markdown
    report_content = []
    report_content.append("# 📊 Reporte Estadístico: Patrones de Rendimiento y Confluencias")
    report_content.append(f"Generado a partir del análisis histórico de **{total_trades} trades** en tu bitácora de trading.\n")
    report_content.append(f"### 📈 Resumen General de Cuenta")
    report_content.append(f"* **Trades Totales:** `{total_trades}`")
    report_content.append(f"* **Victorias (Wins):** `{win_count}`")
    report_content.append(f"* **Derrotas (Losses):** `{loss_count}`")
    report_content.append(f"* **Breakevens (BEs):** `{be_count}`")
    report_content.append(f"* **Win Rate Efectivo (excluyendo BEs):** `{win_rate:.1f}%` \n")
    
    report_content.append("---")
    report_content.append("## 🧠 Patrones de Confluencias Ganadoras vs. Perdedoras")
    report_content.append("Analiza qué factores técnicos aumentan matemáticamente tu probabilidad de éxito:\n")
    report_content.append("| Confluencia Técnica | Usos Totales | Wins | Losses | BEs | Win Rate (%) |")
    report_content.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    
    def _safe_win_rate(item):
        stat = item[1]
        decisions = stat["wins"] + stat["losses"]
        return (stat["wins"] / decisions * 100) if decisions > 0 else 0.0

    sorted_confs = sorted(confluence_stats.items(), key=_safe_win_rate, reverse=True)
    for conf, stat in sorted_confs:
        decisions = stat["wins"] + stat["losses"]
        wr = (stat["wins"] / decisions * 100) if decisions > 0 else 0.0
        report_content.append(f"| **{conf.title()}** | `{stat['total']}` | `{stat['wins']}` | `{stat['losses']}` | `{stat['bes']}` | `{wr:.1f}%` |")
        
    report_content.append("\n---")
    report_content.append("## 🔍 Impacto de la AUSENCIA de Confluencias Clave")
    report_content.append("¿Qué sucede si ignoras un elemento del plan? Estos son los resultados cuando operas **SIN** confluencia:\n")
    report_content.append("| Confluencia Faltante | Trades Operados SIN ella | Wins | Losses | BEs | Win Rate SIN ella (%) | Impacto en tu WR |")
    report_content.append("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    
    for cond, stat in absence_stats.items():
        total_without = stat["total_without"]
        if total_without == 0:
            continue
        decisions_without = stat["wins_without"] + stat["losses_without"]
        wr_without = (stat["wins_without"] / decisions_without * 100) if decisions_without > 0 else 0.0
        
        # Calcular diferencia con el Win Rate general
        diff = wr_without - win_rate
        color = "🔴 Caída" if diff < 0 else "🟢 Subida"
        impact_str = f"{color} de `{abs(diff):.1f}%` en tu WR"
        
        # Resaltar si la caída es seria
        if diff < -15:
            impact_str = f"⚠️ **{impact_str} (Muy Crítico)**"
        elif diff < -5:
            impact_str = f"**{impact_str} (Peligro)**"
            
        report_content.append(f"| **SIN {cond.title()}** | `{total_without}` | `{stat['wins_without']}` | `{stat['losses_without']}` | `{stat['bes_without']}` | `{wr_without:.1f}%` | {impact_str} |")

    report_content.append("\n---")
    report_content.append("## ⚡ Análisis por Mercado (MNQ vs. MES)")
    report_content.append("¿En qué instrumento eres más rentable y eficiente?\n")
    report_content.append("| Instrumento | Trades Totales | Wins | Losses | BEs | Win Rate (%) | Ratio R:R Promedio |")
    report_content.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    for inst, stat in instrument_stats.items():
        decisions = stat["wins"] + stat["losses"]
        wr = (stat["wins"] / decisions * 100) if decisions > 0 else 0.0
        avg_rr = (stat["rr_sum"] / stat["rr_count"]) if stat["rr_count"] > 0 else 0.0
        report_content.append(f"| **{inst}** | `{stat['total']}` | `{stat['wins']}` | `{stat['losses']}` | `{stat['bes']}` | `{wr:.1f}%` | `{avg_rr:.2f} R` |")

    report_content.append("\n---")
    report_content.append("## 📐 Métricas de Precisión MAE y MFE")
    report_content.append("Precisión de tus entradas y eficiencia de tus salidas en ticks promedio:\n")
    report_content.append(f"* **MAE Promedio en Victorias (Drawdown):** `{avg_mae_win:.1f} ticks` (Un MAE bajo indica entradas precisas al instante).")
    report_content.append(f"* **MFE Promedio en Victorias (Recorrido Máximo):** `{avg_mfe_win:.1f} ticks` (Evalúa si tus salidas estructurales dejan dinero en la mesa).")
    report_content.append(f"* **MAE Promedio en Derrotas:** `{avg_mae_loss:.1f} ticks` (Muestra qué tanto permites que el precio vaya en tu contra antes de stop out).")
    report_content.append(f"* **MFE Promedio en Derrotas (Falsas Alarmas):** `{avg_mfe_loss:.1f} ticks` (Muestra si tus trades perdedores estuvieron a favor antes de volverse en contra. Indica si debes ajustar la protección BE).")

    report_content.append("\n---")
    report_content.append("## 🚨 Patrones de Errores y Sesgos Psicológicos")
    report_content.append("Identificación de sesgos de comportamiento redactados en tus notas y su impacto real:\n")
    report_content.append("| Error Conductual Detectado | Sesiones con este Error | Wins | Losses | Win Rate (%) | Estado / Consecuencia |")
    report_content.append("| :--- | :---: | :---: | :---: | :---: | :--- |")
    
    for pattern, stat in behavioral_stats.items():
        decisions = stat["wins"] + stat["losses"]
        wr = (stat["wins"] / decisions * 100) if decisions > 0 else 0.0
        status_str = "🟢 Operable con cuidado" if wr > 50 else "🔴 ALTAMENTE DESTRUCTIVO (Evitar a toda costa)"
        report_content.append(f"| **{pattern.title()}** | `{stat['total']}` | `{stat['wins']}` | `{stat['losses']}` | `{wr:.1f}%` | {status_str} |")

    report_content.append("\n---")
    report_content.append("## 💡 CONCLUSIONES Y PLAN DE ACCIÓN PARA MEJORAR")
    
    # Generar conclusiones dinámicas basadas en los datos
    conclusions = []
    
    # Buscar el mayor impacto negativo
    worst_absence = None
    max_drop = 0
    for cond, stat in absence_stats.items():
        decisions_without = stat["wins_without"] + stat["losses_without"]
        wr_without = (stat["wins_without"] / decisions_without * 100) if decisions_without > 0 else 0.0
        drop = win_rate - wr_without
        if drop > max_drop:
            max_drop = drop
            worst_absence = cond
            
    if worst_absence:
        conclusions.append(f"1. ⚠️ **Regla de Oro:** Operar **SIN {worst_absence.upper()}** destruye tu Win Rate, provocando una caída del `{max_drop:.1f}%` en tu efectividad. A partir de ahora, **{worst_absence.title()}** debe ser una confluencia de carácter **OBLIGATORIO** para autorizar cualquier trade.")
        
    # Comparar NQ vs ES
    if len(instrument_stats) >= 2:
        nq_wr = 0.0
        es_wr = 0.0
        if "NQ" in instrument_stats:
            nq_d = instrument_stats["NQ"]["wins"] + instrument_stats["NQ"]["losses"]
            nq_wr = (instrument_stats["NQ"]["wins"] / nq_d * 100) if nq_d > 0 else 0.0
        if "ES" in instrument_stats:
            es_d = instrument_stats["ES"]["wins"] + instrument_stats["ES"]["losses"]
            es_wr = (instrument_stats["ES"]["wins"] / es_d * 100) if es_d > 0 else 0.0
            
        if abs(nq_wr - es_wr) > 10:
            better = "Nasdaq (NQ)" if nq_wr > es_wr else "S&P 500 (ES)"
            worse = "S&P 500 (ES)" if nq_wr > es_wr else "Nasdaq (NQ)"
            conclusions.append(f"2. ⚡ **Selección de Mercado:** Eres sustancialmente más rentable operando en **{better}** (`{max(nq_wr, es_wr):.1f}%` WR) en comparación con **{worse}** (`{min(nq_wr, es_wr):.1f}%` WR). Considera enfocar el 80% de tus análisis en tu mercado fuerte.")
            
    # MFE en pérdidas
    if avg_mfe_loss > (avg_mae_loss * 0.8):
        conclusions.append("3. 🛡️ **Defensa y Gestión de BE:** En tus operaciones perdedoras, el precio avanza a favor de media un recorrido significativo antes de volverse en contra y tocar el stop. Esto indica que necesitas un protocolo más defensivo de **Breakeven parcial** o ajuste de Stop Loss cuando el precio alcance confluencias de 1:1 R:R.")
        
    # FOMO
    fomo_total = behavioral_stats["fomo / entrada prematura"]["total"]
    if fomo_total > 0:
        fomo_wr = (behavioral_stats["fomo / entrada prematura"]["wins"] / (behavioral_stats["fomo / entrada prematura"]["wins"] + behavioral_stats["fomo / entrada prematura"]["losses"]) * 100) if (behavioral_stats["fomo / entrada prematura"]["wins"] + behavioral_stats["fomo / entrada prematura"]["losses"]) > 0 else 0.0
        if fomo_wr < 30:
            conclusions.append(f"4. 🚨 **Gestión de Impulsividad:** Las operaciones marcadas con sesgo de **FOMO / Entrada Prematura** tienen una tasa de acierto de apenas el `{fomo_wr:.1f}%`. Esperar el cierre de la vela de confirmación y el retesteo estructural no es opcional: entrar antes por miedo a quedarse fuera es una pérdida matemática garantizada.")

    if not conclusions:
        conclusions.append("1. Sigue documentando tus trades con sus confluencias detalladas y MAE/MFE para generar conclusiones con mayor cantidad de datos históricos.")
        
    for concl in conclusions:
        report_content.append(concl)
        
    # Guardar reporte
    markdown_text = "\n".join(report_content)
    
    workspace_report_path = journal_dir / "patterns_report.md"
    with open(workspace_report_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
        
    # Guardar en Gemini
    gemini_workspace = r"C:\Users\rsama\.gemini\antigravity-cli\brain\02cb9977-937b-410d-8eb5-107b2e6261c9"
    if os.path.exists(gemini_workspace):
        gemini_report_path = Path(gemini_workspace) / "patterns_report.md"
        with open(gemini_report_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
    print(f"¡Análisis de patrones completado con éxito!")
    print(f"Reporte de patrones guardado en: {workspace_report_path}")
    if os.path.exists(gemini_workspace):
        print(f"Reporte espejo Gemini actualizado en: {gemini_report_path}")

if __name__ == "__main__":
    analyze_patterns()
