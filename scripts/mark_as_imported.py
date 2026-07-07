#!/usr/bin/env python3
# encoding: utf-8
"""Script to update status of a video in import_queue.json."""

import sys
import json
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/mark_as_imported.py <video_id> <status> [concept_file_path]", file=sys.stderr)
        sys.exit(1)
        
    video_id = sys.argv[1]
    status = sys.argv[2] # "imported", "failed", "pending"
    concept_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    vault_root = Path(__file__).parent.parent
    queue_file = vault_root / "scratch" / "import_queue.json"
    
    if not queue_file.exists():
        print(f"Error: No se encontró la cola en: {queue_file}", file=sys.stderr)
        sys.exit(1)
        
    try:
        data = json.loads(queue_file.read_text(encoding="utf-8"))
        
        found = False
        for v in data:
            if v["video_id"] == video_id:
                v["status"] = status
                if concept_file:
                    v["concept_file"] = concept_file
                found = True
                break
                
        if found:
            queue_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Video {video_id} actualizado con éxito a status: {status}")
        else:
            print(f"Error: Video ID {video_id} no se encontró en la cola.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error al actualizar la cola: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
