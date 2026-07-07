#!/usr/bin/env python3
# encoding: utf-8
"""Script to extract all video IDs/URLs from a YouTube playlist URL."""

import sys
import re
import urllib.request
import urllib.parse
import json
from pathlib import Path

def extract_playlist_id(url):
    """Extrae el ID de la playlist a partir de la URL."""
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None

def fetch_playlist_videos(playlist_id):
    """Descarga la página de la playlist y extrae los IDs de los videos usando regex."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
        # Buscar todas las coincidencias de "videoId":"ID" en el JSON ytInitialData de la página
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        
        # Deduplicar preservando el orden original
        seen = set()
        dedup_ids = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                dedup_ids.append(vid)
                
        return dedup_ids
    except Exception as e:
        print(f"Error al descargar o parsear la playlist: {e}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/get_youtube_playlist.py <URL_de_Playlist_de_YouTube>", file=sys.stderr)
        sys.exit(1)
        
    url = sys.argv[1]
    playlist_id = extract_playlist_id(url)
    
    if not playlist_id:
        print(f"Error: No se pudo extraer el ID de la playlist de: {url}", file=sys.stderr)
        sys.exit(1)
        
    print(f"ID de Playlist Detectado: {playlist_id}")
    print("Obteniendo lista de videos desde YouTube...")
    
    video_ids = fetch_playlist_videos(playlist_id)
    
    if not video_ids:
        print("Error: No se pudieron extraer videos de esta playlist (puede ser privada o estar vacía).", file=sys.stderr)
        sys.exit(1)
        
    print(f"Se encontraron {len(video_ids)} videos en la playlist.")
    
    # Guardar la lista de IDs en un archivo txt para procesamiento
    vault_root = Path(__file__).parent.parent
    scratch_dir = vault_root / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    output_file = scratch_dir / "playlist_videos.json"
    
    # Guardar como JSON estructurado con títulos temporales (URLs completas)
    playlist_data = {
        "playlist_id": playlist_id,
        "videos": [{"video_id": vid, "url": f"https://www.youtube.com/watch?v={vid}"} for vid in video_ids]
    }
    
    output_file.write_text(json.dumps(playlist_data, indent=2), encoding="utf-8")
    print(f"Lista de videos guardada en: {output_file}")
    
    # Imprimir resumen de los primeros 10 videos
    for idx, vid in enumerate(video_ids[:10]):
        print(f"  {idx+1}. https://www.youtube.com/watch?v={vid}")
    if len(video_ids) > 10:
        print(f"  ... y {len(video_ids) - 10} videos más.")

if __name__ == '__main__':
    main()
