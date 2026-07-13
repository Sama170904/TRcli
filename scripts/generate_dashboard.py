#!/usr/bin/env python3
# encoding: utf-8
"""Script to automatically regenerate dashboard.md based on journal.json and bitacoras session files."""

import os
import re
import json
from pathlib import Path
from datetime import datetime

def get_day_of_week_spanish(date_str):
    """Devuelve el nombre del día de la semana en español."""
    days = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo"
    }
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return days[dt.weekday()]
    except Exception:
        return "N/A"

def parse_session_frontmatter(content):
    """Parsea el frontmatter YAML de la bitácora de sesión."""
    pnl = 0.0
    trades_count = 0
    result = "NO OPERADO"
    
    # Intentar parsear frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_content = fm_match.group(1)
        for line in fm_content.splitlines():
            if ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                if k == "pnl":
                    try:
                        pnl = float(v)
                    except ValueError:
                        pass
                elif k == "trades_count":
                    try:
                        trades_count = int(v)
                    except ValueError:
                        pass
                elif k == "result":
                    result = v.replace('"', '').replace("'", '').upper()
        return pnl, trades_count, result

    # Fallback si no hay frontmatter
    for line in content.splitlines():
        if "resultado neto" in line.lower():
            match = re.search(r"([+-]?\s*\$?\s*\d+(?:\.\d+)?)", line)
            if match:
                pnl = float(match.group(1).replace("$", "").replace(" ", ""))
        elif "trades realizados" in line.lower():
            match = re.search(r"(\d+)", line)
            if match:
                trades_count = int(match.group(1))
        elif "resultado:" in line.lower():
            if "win" in line.lower():
                result = "WIN"
            elif "loss" in line.lower():
                result = "LOSS"
            elif "be" in line.lower():
                result = "BE"
                
    return pnl, trades_count, result

def main():
    print("Iniciando regeneración automática de dashboard.md...")
    
    root_dir = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal")
    journal_path = root_dir / "journal.json"
    bitacoras_dir = root_dir / "bitacoras"
    dashboard_path = root_dir / "dashboard.md"
    
    if not journal_path.exists():
        print("Error: No se encontró journal.json.")
        return
    if not bitacoras_dir.exists():
        print("Error: No se encontró la carpeta bitacoras.")
        return

    # 1. Leer trades de journal.json para estadísticas de trades individuales
    try:
        trades = json.loads(journal_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error al leer journal.json: {e}")
        return

    total_trades = len(trades)
    wins_trades = sum(1 for t in trades if t.get("result") == "Win")
    losses_trades = sum(1 for t in trades if t.get("result") == "Loss")
    be_trades = sum(1 for t in trades if t.get("result") == "BE")
    win_rate_trades = (wins_trades / total_trades * 100) if total_trades > 0 else 0.0

    # 2. Leer todas las bitácoras de sesión para estadísticas de sesión
    session_files = sorted(bitacoras_dir.glob("*_session.md"), reverse=True)
    sessions_data = []
    
    total_pnl = 0.0
    win_sessions = 0
    loss_sessions = 0
    be_sessions = 0
    no_trade_sessions = 0
    
    for f in session_files:
        # Extraer fecha del nombre del archivo: YYYY-MM-DD_session.md -> YYYY-MM-DD
        date_match = re.match(r"^(\d{4}-\d{2}-\d{2})_session\.md$", f.name)
        if not date_match:
            continue
        date_str = date_match.group(1)
        
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
            
        pnl, trades_count, result = parse_session_frontmatter(content)
        
        # Formatear fecha para el dashboard (DD/MM/YYYY)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%d/%m/%Y")
        
        day_of_week = get_day_of_week_spanish(date_str)
        
        sessions_data.append({
            "date": formatted_date,
            "day": day_of_week,
            "pnl": pnl,
            "trades": trades_count,
            "result": result,
            "file_name": f.name
        })
        
        total_pnl += pnl
        if result == "WIN":
            win_sessions += 1
        elif result == "LOSS":
            loss_sessions += 1
        elif result == "BE":
            be_sessions += 1
        else:
            no_trade_sessions += 1

    total_sessions = len(sessions_data)
    
    # Calcular porcentajes de efectividad de sesión
    pct_win = (win_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
    pct_loss = (loss_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
    pct_be = (be_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
    pct_no_trade = (no_trade_sessions / total_sessions * 100) if total_sessions > 0 else 0.0

    # 3. Datos de cuenta fondeada (Performance Account)
    # Offset para alinear el PnL acumulado histórico con el balance real de la cuenta PA ($50,837.00 USD actual)
    current_balance = 46500.75 + total_pnl

    # 4. Generar el reporte del dashboard.md
    report = []
    report.append("# DASHBOARD GENERAL DE TRADING")
    report.append("================================================================================")
    report.append("Este es el centro de control y registro de rendimiento de mis sesiones de trading.")
    report.append("Mantiene el acumulado histórico y los enlaces rápidos a las bitácoras diarias.\n")
    report.append("--- \n")
    
    report.append("## 🏆 ESTATUS DE LA CUENTA FONDEADA (PA)")
    report.append(f"* **Tipo de Cuenta:** Performance Account (PA - Real)")
    report.append(f"* **Balance Actual:** `${current_balance:,.2f} USD` (al {datetime.now().strftime('%d/%m/%Y')})")
    report.append(f"* **Estado de la Cuenta:** Activa y Operando 🟢\n")
    report.append("--- \n")
    
    report.append("## 📈 ESTADÍSTICAS GENERALES DE LA CUENTA")
    pnl_sign = "+" if total_pnl >= 0 else ""
    report.append(f"* **Balance Neto Total (Bitácora):** `{pnl_sign}${total_pnl:,.2f} USD`")
    report.append(f"* **Total Sesiones Operadas:** `{total_sessions}`")
    report.append(f"* **Sesiones Ganadoras (Win):** `{win_sessions}` ({pct_win:.1f}% de efectividad de sesión)")
    report.append(f"* **Sesiones en Breakeven (BE):** `{be_sessions}` ({pct_be:.1f}% de efectividad de sesión)")
    report.append(f"* **Sesiones Perdedoras (Loss):** `{loss_sessions}` ({pct_loss:.1f}% de efectividad de sesión)")
    report.append(f"* **Sesiones sin Operar (No Trade):** `{no_trade_sessions}` ({pct_no_trade:.1f}% de efectividad de sesión)")
    report.append(f"* **Total Trades Ejecutados:** `{total_trades}`")
    report.append(f"  - *Trades Ganadores:* `{wins_trades}`")
    report.append(f"  - *Trades en Breakeven (BE):* `{be_trades}`")
    report.append(f"  - *Trades Perdedores (SL):* `{losses_trades}`")
    report.append(f"* **Win Rate de Trades:** `{win_rate_trades:.1f}%` ({wins_trades}/{total_trades})\n")
    report.append("--- \n")
    
    report.append("## 📅 REGISTRO HISTÓRICO DE SESIONES\n")
    report.append("| Fecha | Día | PnL Neto (USD) | Trades | Resultado | Enlace a Bitácora Diaria |")
    report.append("| :--- | :---: | :--- | :---: | :---: | :--- |")
    
    for s in sessions_data:
        pnl_val = s["pnl"]
        pnl_sign = "+" if pnl_val > 0 else ""
        pnl_str = f"**{pnl_sign}${pnl_val:,.2f}**" if pnl_val != 0 else f"${pnl_val:,.2f}"
        
        result_icon = "⚪ NO TRADE"
        if s["result"] == "WIN":
            result_icon = "🟢 WIN"
        elif s["result"] == "LOSS":
            result_icon = "🔴 LOSS"
        elif s["result"] == "BE":
            result_icon = "⚪ BE"
            
        file_name = s["file_name"]
        link = f"[Bitácora {s['date'].replace('/', '-')}](file:///C:/Users/rsama/Documents/proyecto-geminicli/trading-journal/bitacoras/{file_name})"
        
        report.append(f"| **{s['date']}** | {s['day']} | {pnl_str} | {s['trades']} | {result_icon} | {link} |")
        
    report.append("\n--- \n")
    report.append("## 📝 INSTRUCCIONES PARA ACTUALIZAR EL DIARIO")
    report.append("1. Guardar la captura de pantalla de la sesión en la carpeta: `trading-journal/imagenes/YYYY-MM-DD_chart.png`")
    report.append("2. Crear el archivo de sesión diaria en: `trading-journal/bitacoras/YYYY-MM-DD_session.md`")
    report.append("3. Rellenar los apartados de: Análisis HTF, Análisis de Trades, y Psicología de la Sesión.")
    report.append("4. **Este archivo se actualizará automáticamente** leyendo el historial de `journal.json` y tus bitácoras.")
    
    # Escribir de vuelta
    dashboard_path.write_text("\n".join(report), encoding="utf-8")
    print("¡Éxito! Dashboard general actualizado correctamente.")

if __name__ == '__main__':
    main()
