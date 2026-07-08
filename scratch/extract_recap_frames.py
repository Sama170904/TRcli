#!/usr/bin/env python3
# encoding: utf-8
"""Script to extract specific frames from the downloaded trade recap video."""

import cv2
import os
from pathlib import Path

def extract_frame_at_second(cap, fps, second, output_path):
    # Calcular número de frame
    frame_number = int(fps * second)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(str(output_path), frame)
        print(f"Extraído frame del segundo {second} ({int(second//60)}m{int(second%60)}s) -> {output_path.name}")
        return True
    else:
        print(f"Error al extraer frame en segundo {second}")
        return False

def main():
    video_path = Path(r"C:\Users\rsama\Downloads\How I Made 15,302 Day Trading In 10 SECONDS (I'M IN FLOW STATE) - PB Blake Trades (720p, h264).mp4")
    scratch_dir = Path(r"C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\scratch")
    
    if not video_path.exists():
        print(f"Error: No se encontró el archivo de video en {video_path}")
        return
        
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Error al abrir el archivo de video.")
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps
    
    print(f"Video cargado con éxito:")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duración: {duration:.2f} segundos ({int(duration//60)}m{int(duration%60)}s)")
    
    # Extraer de 7:45 (465s) a 8:20 (500s) cada 5 segundos
    seconds_to_extract = list(range(465, 501, 5))
    
    for sec in seconds_to_extract:
        minutes = int(sec // 60)
        seconds = int(sec % 60)
        out_name = f"recap_frame_{minutes}m{seconds:02d}s.jpg"
        out_path = scratch_dir / out_name
        extract_frame_at_second(cap, fps, sec, out_path)
        
    cap.release()
    print("Extracción de frames concluida con éxito.")

if __name__ == '__main__':
    main()
