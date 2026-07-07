#!/usr/bin/env python3
# encoding: utf-8
"""Script to extract YouTube transcripts and save them to a scratch file."""

import sys
import os
import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    """Extrae el ID del video de YouTube a partir de la URL."""
    # Patrones comunes de URL de YouTube
    patterns = [
        r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/|\/watch\?v=|\&v=)([^#\&\?]*)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # Asegurar que tenga la longitud correcta de un ID de YouTube (habitualmente 11 caracteres)
            if len(video_id) == 11:
                return video_id
    return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/get_youtube_transcript.py <URL_o_ID_de_YouTube>", file=sys.stderr)
        sys.exit(1)
        
    target = sys.argv[1]
    video_id = extract_video_id(target) if "youtube.com" in target or "youtu.be" in target else target
    
    if not video_id:
        print(f"Error: No se pudo extraer el ID del video de: {target}", file=sys.stderr)
        sys.exit(1)
        
    print(f"ID del Video Detectado: {video_id}")
    
    try:
        # Instanciar el cliente API
        api = YouTubeTranscriptApi()
        # Intentar obtener la transcripción en español o inglés
        transcript_list = api.list(video_id)
        
        # Buscar español primero, luego inglés, luego cualquier idioma disponible
        transcript = None
        try:
            transcript = transcript_list.find_transcript(['es'])
            print("Transcripción encontrada en Español (es).")
        except Exception:
            try:
                transcript = transcript_list.find_transcript(['en'])
                print("Transcripción en español no disponible. Usando Inglés (en).")
            except Exception:
                # Si no hay español ni inglés, obtener la primera disponible
                for t in transcript_list:
                    transcript = t
                    print(f"Usando transcripción en: {t.language} ({t.language_code})")
                    break
        
        if not transcript:
            print("Error: No se encontraron transcripciones disponibles.", file=sys.stderr)
            sys.exit(1)
            
        # Descargar los datos de la transcripción
        data = transcript.fetch()
        
        # Unir todos los fragmentos de texto en una sola cadena estructurada con tiempos
        raw_lines = []
        full_text = []
        
        for entry in data:
            text = entry.text.strip()
            start = entry.start
            # Convertir start seconds a MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            raw_lines.append(f"{timestamp} {text}")
            full_text.append(text)
            
        # Crear directorio scratch si no existe
        vault_root = Path(__file__).parent.parent
        scratch_dir = vault_root / "scratch"
        scratch_dir.mkdir(exist_ok=True)
        
        # Guardar la transcripción cruda formateada con marcas de tiempo
        output_file = scratch_dir / "raw_transcript.txt"
        output_file.write_text("\n".join(raw_lines), encoding="utf-8")
        
        print(f"Transcripción extraída y guardada exitosamente en: {output_file}")
        print(f"Total de líneas extraídas: {len(raw_lines)}")
        
    except Exception as e:
        print(f"Error al descargar la transcripción del video: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
