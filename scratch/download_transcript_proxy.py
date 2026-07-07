import sys
import os
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from curl_cffi import requests as requests_cffi

PROXIES = [
    {"http": "http://180.191.59.56:8081", "https": "http://180.191.59.56:8081"},
    {"http": "http://38.156.14.131:999", "https": "http://38.156.14.131:999"},
    {"http": "http://183.88.213.178:8080", "https": "http://183.88.213.178:8080"},
    {"http": "http://188.132.150.47:8080", "https": "http://188.132.150.47:8080"},
    None
]

def main():
    if len(sys.argv) < 2:
        print("Usage: python scratch/download_transcript_proxy.py <video_id>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    print(f"Starting proxy-based transcript downloader for {video_id}...")
    
    success = False
    for i, proxy in enumerate(PROXIES):
        proxy_desc = f"Proxy {proxy}" if proxy else "No proxy"
        print(f"Trying with {proxy_desc}...")
        try:
            # Let's try curl_cffi session first, then fallback to requests session
            # Since youtube_transcript_api internally expects requests.Session, passing a requests_cffi session works if it duck-types correctly.
            # If not, we'll try standard requests session with proxy.
            try:
                print("Trying curl_cffi Session...")
                session = requests_cffi.Session()
                if proxy:
                    session.proxies = proxy
                # Impersonate chrome
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                })
                api = YouTubeTranscriptApi(http_client=session)
                transcript_list = api.list(video_id)
            except Exception as e_cffi:
                print(f"curl_cffi failed: {e_cffi}. Trying standard requests Session...")
                session = requests.Session()
                if proxy:
                    session.proxies = proxy
                api = YouTubeTranscriptApi(http_client=session)
                transcript_list = api.list(video_id)
                
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['es'])
                print("Found Spanish transcript.")
            except Exception:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    print("Found English transcript.")
                except Exception:
                    for t in transcript_list:
                        transcript = t
                        print(f"Found transcript in: {t.language}")
                        break
            
            if not transcript:
                print("No transcript found in list.")
                continue
                
            data = transcript.fetch()
            
            raw_lines = []
            for entry in data:
                text = entry['text'].strip() if isinstance(entry, dict) else entry.text.strip()
                start = entry['start'] if isinstance(entry, dict) else entry.start
                minutes = int(start // 60)
                seconds = int(start % 60)
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                raw_lines.append(f"{timestamp} {text}")
                
            vault_root = Path(__file__).parent.parent
            scratch_dir = vault_root / "scratch"
            scratch_dir.mkdir(exist_ok=True)
            
            output_file = scratch_dir / "raw_transcript.txt"
            output_file.write_text("\n".join(raw_lines), encoding="utf-8")
            
            print(f"Successfully saved {len(raw_lines)} lines to {output_file} using {proxy_desc}!")
            success = True
            break
        except Exception as e:
            print(f"Failed using {proxy_desc}: {e}")
            
    if not success:
        print("Error: All proxies failed to fetch transcript.")
        sys.exit(1)

if __name__ == '__main__':
    main()
