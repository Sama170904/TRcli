import os
import re
import json
from pathlib import Path

def parse_pnl(pnl_str):
    # Intentar extraer números y signo de cadenas como "+$600.00 USD", "$0.00", "-$150"
    pnl_str = pnl_str.replace("USD", "").replace("$", "").replace(",", "").strip()
    match = re.search(r"([+-]?\d+(?:\.\d+)?)", pnl_str)
    if match:
        return float(match.group(1))
    return 0.0

def main():
    print("Iniciando analizador de bitácoras para Red Neuronal de Trading...")
    
    script_dir = Path(__file__).parent.resolve()
    journal_dir = script_dir.parent
    bitacoras_dir = journal_dir / "bitacoras"
    
    if not bitacoras_dir.exists():
        print(f"Error: La carpeta de bitácoras no existe en {bitacoras_dir}")
        return
        
    session_files = sorted(bitacoras_dir.glob("*_session.md"))
    
    total_sessions = 0
    total_pnl = 0.0
    wins = 0
    losses = 0
    bes = 0
    
    recent_lessons = []
    frequent_errors = []
    
    # Expresiones regulares para parsear datos clave
    lessons_re = re.compile(r"### 🧠 (?:LECCIONES DE LA SESIÓN DE HOY|LECCIONES)(.*?)(?=\n###|\n==|\Z)", re.DOTALL | re.IGNORECASE)
    
    # Palabras clave para detectar errores psicológicos comunes
    error_keywords = {
        "FOMO": ["fomo", "fuerzo", "ansiedad", "perder el movimiento", "ruptura"],
        "Sobreoperar (Overtrading)": ["sobreoperar", "muchos trades", "varios trades", "forzar"],
        "Ignorar Resistencia": ["resistencia", "ignorar ob", "ignorar fvg"],
        "Mover Stop Loss a BE prematuro": ["be prematuro", "sacar en be", "breakeven antes", "muevo a be"],
        "Operar fuera de la Killzone": ["fuera de killzone", "fuera de horario", "killzone tarde", "antes de killzone"]
    }
    
    error_counts = {k: 0 for k in error_keywords.keys()}
    
    for f in session_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error leyendo {f.name}: {e}")
            continue
            
        total_sessions += 1
        
        # Parsear PnL línea por línea para mayor robustez
        for line in content.splitlines():
            if "resultado neto" in line.lower():
                # Encontrar cualquier número (incluido signo + o - y decimales)
                match = re.search(r"([+-]?\s*\$?\s*\d+(?:\.\d+)?)", line)
                if match:
                    val_str = match.group(1).replace("$", "").replace(" ", "")
                    val = float(val_str)
                    total_pnl += val
                    if val > 0.0:
                        wins += 1
                    elif val < 0.0:
                        losses += 1
                    else:
                        bes += 1
                break
                
        # Parsear Lecciones
        lessons_match = lessons_re.search(content)
        if lessons_match:
            raw_lessons = lessons_match.group(1).strip()
            # Dividir por líneas de lista (ej: 1. o - o *)
            lines = [l.strip() for l in re.split(r"\n\s*(?:\d+\.|\-|\*)\s*", raw_lessons) if l.strip()]
            for line in lines[:3]:  # Tomar las 3 principales lecciones
                # Limpiar texto
                clean_line = re.sub(r"\*\*?", "", line)
                if clean_line not in recent_lessons:
                    recent_lessons.append(clean_line)
                    
        # Escaneo de palabras clave de errores psicológicos en todo el texto de la sesión
        content_lower = content.lower()
        for error_name, keywords in error_keywords.items():
            for kw in keywords:
                if kw in content_lower:
                    error_counts[error_name] += 1
                    break  # Contar solo una vez por archivo
                    
    # Determinar advertencias basadas en la frecuencia de errores detectados
    sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
    warnings = []
    for err, count in sorted_errors:
        if count > 0:
            pct = (count / total_sessions) * 100 if total_sessions > 0 else 0
            warnings.append({
                "error": err,
                "count": count,
                "percentage": round(pct, 1)
            })
            
    # Mantener lecciones recientes compactas (máximo 6)
    recent_lessons = recent_lessons[-6:]
    
    profile = {
        "total_sessions": total_sessions,
        "total_pnl": round(total_pnl, 2),
        "wins": wins,
        "losses": losses,
        "breakevens": bes,
        "win_rate_sessions": round((wins / total_sessions * 100), 1) if total_sessions > 0 else 0.0,
        "recent_lessons": recent_lessons,
        "warnings": warnings
    }
    
    profile_path = script_dir / "psych_profile.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        
    print(f"¡Análisis completado! Perfil de riesgo psicológico guardado en: {profile_path}")
    print(f"Sesiones analizadas: {total_sessions} | PnL Total: ${total_pnl:.2f} USD")
    if len(warnings) > 0:
        print("Errores más frecuentes detectados:")
        for w in warnings[:2]:
            print(f" - {w['error']}: presente en el {w['percentage']}% de las sesiones.")

if __name__ == "__main__":
    main()
