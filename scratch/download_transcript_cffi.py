import sys
import os
import re
import traceback
from pathlib import Path

# Monkey-patch requests with curl_cffi before importing youtube_transcript_api
import requests
from curl_cffi import requests as requests_cffi

class PatchedSession(requests_cffi.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        })

requests.Session = PatchedSession
requests.get = requests_cffi.get
requests.post = requests_cffi.post

from youtube_transcript_api import YouTubeTranscriptApi

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_transcript_cffi.py <video_id>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    print(f"Patched Downloader: Fetching transcript for {video_id}...")
    
    try:
        api = YouTubeTranscriptApi()
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
            print("Error: No transcript found.")
            sys.exit(1)
            
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
        
        print(f"Successfully saved {len(raw_lines)} lines to {output_file}")
        
    except Exception as e:
        print(f"Failed to fetch transcript: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
