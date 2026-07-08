import urllib.parse
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from curl_cffi import requests

def main():
    video_id = "1r4RxjJkMV4"
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    session = requests.Session()
    print("Fetching watch page...")
    response = session.get(url, headers=headers, impersonate="chrome120")
    if response.status_code != 200:
        print("Failed to fetch watch page")
        return
        
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', response.text)
    if not match:
        match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', response.text)
    if not match:
        print("Failed to find player response")
        return
        
    player_response = json.loads(match.group(1))
    captions = player_response.get("captions", {})
    tracklist = captions.get("playerCaptionsTracklistRenderer", {})
    caption_tracks = tracklist.get("captionTracks", [])
    
    if not caption_tracks:
        print("No caption tracks found")
        return
        
    selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'es'), None)
    if not selected_track:
        selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'en'), None)
    if not selected_track:
        selected_track = caption_tracks[0]
        
    track_url = selected_track.get('baseUrl')
    print(f"Selected track language: {selected_track.get('languageCode')}")
    
    # Download XML using the same session
    print("Downloading XML via curl_cffi Session...")
    response_xml = session.get(track_url, headers=headers, impersonate="chrome120")
    if response_xml.status_code != 200:
        print(f"Failed to fetch XML, status code: {response_xml.status_code}")
        print(response_xml.text[:200])
        return
        
    root = ET.fromstring(response_xml.text)
    raw_lines = []
    for text_elem in root.findall('text'):
        text = text_elem.text
        if not text:
            text = "".join(text_elem.itertext())
        text = text.strip().replace('\n', ' ')
        
        start = float(text_elem.attrib.get('start', '0'))
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        raw_lines.append(f"{timestamp} {text}")
        
    output_path = Path("scratch/recap_transcript.txt")
    output_path.write_text("\n".join(raw_lines), encoding="utf-8")
    print(f"Wrote {len(raw_lines)} lines to {output_path}")

if __name__ == '__main__':
    main()
