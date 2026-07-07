#!/usr/bin/env python3
# encoding: utf-8
"""Script to migrate journal.json fields from strings to native numeric float types."""

import json
from pathlib import Path

def migrate_field(value):
    """Convierte un valor string a float de forma segura."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Si es string, limpiar y convertir
    val_str = str(value).strip()
    if not val_str or val_str.upper() in ["N/A", "NONE", "NULL", "BE", "LOSS", "WIN"]:
        return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def main():
    root_dir = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal")
    journal_path = root_dir / "journal.json"
    
    if not journal_path.exists():
        print("Error: No se encontró journal.json.")
        return
        
    try:
        trades = json.loads(journal_path.read_text(encoding="utf-8"))
        print(f"Cargando {len(trades)} trades para migración...")
        
        migrated_count = 0
        for t in trades:
            # Lista de campos numéricos a normalizar
            numeric_fields = ["entry", "sl", "tp", "exit", "rr", "mae", "mfe"]
            for field in numeric_fields:
                if field in t:
                    orig = t[field]
                    t[field] = migrate_field(orig)
            migrated_count += 1
            
        # Guardar de vuelta
        journal_path.write_text(
            json.dumps(trades, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"¡Éxito! Se migraron correctamente {migrated_count} trades a tipos numéricos nativos.")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")

if __name__ == '__main__':
    main()
