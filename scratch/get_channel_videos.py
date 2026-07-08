import urllib.request
import re
import json

def main():
    url = "https://www.youtube.com/@pb.blake/videos"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            
            # Busquemos los bloques de ytInitialData para extraer la información estructurada
            match = re.search(r'ytInitialData\s*=\s*({.*?});', html)
            if match:
                data = json.loads(match.group(1))
                # Guardar el JSON estructurado para inspección rápida si queremos
                # Busquemos los videos en el JSON
                video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                # Busquemos los títulos correspondientes
                print(f"Total video IDs found: {len(video_ids)}")
                print(f"Unique video IDs: {list(set(video_ids))[:10]}")
            else:
                print("Failed to parse ytInitialData")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
