#!/usr/bin/env python3
# encoding: utf-8
"""Script to read psych_profile.json and generate active defensive guidelines for startup."""

import json
from pathlib import Path

def main():
    root_dir = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal")
    profile_file = root_dir / "scripts" / "psych_profile.json"
    shield_file = root_dir / "scratch" / "active_shield.md"
    
    if not profile_file.exists():
        # Crear un perfil dummy si no existe
        dummy_profile = {
            "total_sessions": 0,
            "total_pnl": 0.0,
            "errors": {}
        }
        profile_file.write_text(json.dumps(dummy_profile, indent=2), encoding="utf-8")
        
    try:
        profile_data = json.loads(profile_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error al leer perfil psicológico: {e}")
        return
        
    warnings = profile_data.get("warnings", [])
    
    # Ordenar los errores por count descendente
    sorted_errors = sorted(warnings, key=lambda x: x.get("count", 0), reverse=True)
    
    shield_content = []
    shield_content.append("# 🛡️ ESCUDO PROTECTOR ACTIVO — RECOMENDACIONES CONDUCTUALES")
    shield_content.append("Este escudo se genera dinámicamente analizando tus debilidades y errores de las últimas sesiones para proteger tu capital hoy.\n")
    
    if not sorted_errors:
        shield_content.append("> [!NOTE]")
        shield_content.append("> **Historial Limpio:** No se registran errores graves recurrentes en tu perfil. Mantén una ejecución limpia y apegada a la estructura de mercado.")
    else:
        shield_content.append("> [!IMPORTANT]")
        shield_content.append("> **ALERTAS CONDUCTUALES CRÍTICAS PARA HOY:**")
        
        # Listar los dos errores más críticos
        for err_info in sorted_errors[:2]:
            err_name = err_info.get("error", "Unknown")
            count = err_info.get("count", 0)
            percentage = err_info.get("percentage", 0.0)
            
            shield_content.append(f"> *   **{err_name.upper()}** (Detectado en {percentage}% de las sesiones - {count} veces):")
            
            # Directivas específicas por tipo de error
            if "fomo" in err_name.lower():
                shield_content.append(">     *   *Acción Correctiva:* Queda **estrictamente prohibido** entrar a mercado. Si el precio se desplaza sin ti, espera un retroceso ordenado al 50% (Equilibrium) del FVG en vela de 5m. Si no retrocede, no hay trade hoy.")
            elif "chasing" in err_name.lower():
                shield_content.append(">     *   *Acción Correctiva:* No persigas velas de alta velocidad. Toda orden de entrada debe ser **límite (limit order)** colocada en discount/premium del rango de la vela gatillo.")
            elif "resistencia" in err_name.lower() or "soporte" in err_name.lower():
                shield_content.append(">     *   *Acción Correctiva:* Antes de abrir un corto/largo, verifica que no estés comprando en un soporte macro roto ni vendiendo contra una resistencia institucional intacta. Consulta el mapa de liquidez y no operes en el vacío.")
            elif "sobreoperar" in err_name.lower() or "overtrading" in err_name.lower():
                shield_content.append(">     *   *Acción Correctiva:* Limita tu sesión a **máximo 1 o 2 trades de alta confluencia**. Si tocas stop loss en el primer trade, reduce el lote al 50% para el segundo. Si el segundo falla, la sesión termina.")
            else:
                shield_content.append(">     *   *Acción Correctiva:* Aplica las reglas del manual operativo al pie de la letra y protege el Stop Loss detrás de la estructura de anulación.")
                
    shield_content.append("\n## ⚖️ Reglas Operativas Inquebrantables (Reminder)")
    shield_content.append("- **Pérdida Máxima Diaria:** Si tocas tu límite de pérdida diaria, la sesión se cierra de forma inmediata.")
    shield_content.append("- **Filtro de Tendencia (Regla 3 de AGENTS.md):** En días de Expansión, opera únicamente a favor de la tendencia. Queda prohibido buscar contratendencias.")
    
    # Escribir el escudo
    shield_file.write_text("\n".join(shield_content), encoding="utf-8")
    print(f"Escudo protector conductual actualizado y guardado en: {shield_file}")

if __name__ == '__main__':
    main()
