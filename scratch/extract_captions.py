import urllib.request
import re
import json
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def get_transcript(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # Find ytInitialPlayerResponse
        match = re.search(r"ytInitialPlayerResponse\s*=\s*({.*?});", html)
        if not match:
            # Try without semicolon or different format
            match = re.search(r"ytInitialPlayerResponse\s*=\s*({.*?})\s*</script>", html)
            
        if not match:
            print("ytInitialPlayerResponse not found in HTML")
            return None
            
        player_response = json.loads(match.group(1))
        captions = player_response.get("captions", {})
        renderer = captions.get("playerCaptionsTracklistRenderer", {})
        tracks = renderer.get("captionTracks", [])
        
        if not tracks:
            print("No caption tracks found in player response")
            return None
            
        # Prioritize Spanish (es), then English (en), then first available
        track_url = None
        for lang in ['es', 'en']:
            for t in tracks:
                if t.get("languageCode") == lang:
                    track_url = t.get("baseUrl")
                    print(f"Found track for language: {lang}")
                    break
            if track_url:
                break
                
        if not track_url:
            track_url = tracks[0].get("baseUrl")
            print(f"Using default track language: {tracks[0].get('languageCode')}")
            
        # Fetch the XML transcript
        xml_req = urllib.request.Request(
            track_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(xml_req) as xml_resp:
            xml_data = xml_resp.read().decode('utf-8', errors='ignore')
            
        # Parse XML
        root = ET.fromstring(xml_data)
        raw_lines = []
        for text_elem in root.findall('text'):
            text = text_elem.text or ""
            text = text.strip().replace("\n", " ")
            start = float(text_elem.get('start', 0))
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            raw_lines.append(f"{timestamp} {text}")
            
        # Write to raw_transcript.txt
        output_path = Path("scratch/raw_transcript.txt")
        output_path.write_text("\n".join(raw_lines), encoding="utf-8")
        print(f"Successfully wrote transcript to {output_path}. Lines: {len(raw_lines)}")
        return True
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_captions.py <video_id>")
        sys.exit(1)
    vid = sys.argv[1]
    success = get_transcript(vid)
    if not success:
        sys.exit(1)
