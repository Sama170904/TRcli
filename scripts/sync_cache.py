#!/usr/bin/env python3
# encoding: utf-8
"""Script to cache markdown file hashes (SHA-256) to identify changes in the vault."""

import os
import json
import hashlib
from pathlib import Path

def calculate_sha256(file_path):
    """Calcula el hash SHA-256 de un archivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error al calcular hash para {file_path}: {e}")
        return None

def main():
    root_dir = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal")
    scratch_dir = root_dir / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    cache_file = scratch_dir / "vault_cache.json"
    
    # Cargar cache anterior si existe
    old_cache = {}
    if cache_file.exists():
        try:
            old_cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    new_cache = {}
    modified_files = []
    
    # Directorios a monitorear
    directories_to_scan = [
        root_dir / "01-concepts",
        root_dir / "bitacoras"
    ]
    
    for folder in directories_to_scan:
        if not folder.exists():
            continue
        for file_path in folder.rglob("*.md"):
            # Omitir archivos temporales o de cache
            if ".system_generated" in file_path.parts:
                continue
            
            relative_path = file_path.relative_to(root_dir).as_posix()
            current_hash = calculate_sha256(file_path)
            
            if current_hash:
                new_cache[relative_path] = current_hash
                # Si no existía en cache o si el hash cambió, se marca como modificado
                if relative_path not in old_cache or old_cache[relative_path] != current_hash:
                    modified_files.append(relative_path)
                    
    # Guardar nueva cache
    cache_file.write_text(json.dumps(new_cache, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("=== Sincronización de Cache de Bóveda ===")
    print(f"Total de archivos monitoreados: {len(new_cache)}")
    print(f"Archivos modificados/nuevos detectados: {len(modified_files)}")
    
    if modified_files:
        print("\nLista de archivos modificados:")
        for f in modified_files[:10]:
            print(f"  - {f}")
        if len(modified_files) > 10:
            print(f"  ... y {len(modified_files) - 10} más.")
            
    # Escribir lista de modificados a un archivo temporal para que Antigravity lo lea si lo necesita
    modified_list_file = scratch_dir / "modified_files.json"
    modified_list_file.write_text(json.dumps(modified_files, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == '__main__':
    main()
