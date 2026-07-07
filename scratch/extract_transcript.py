import sys
import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from curl_cffi import requests

def extract_caption_tracks(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Fetching YouTube page for {video_id}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    response = requests.get(url, headers=headers, impersonate="chrome120")
    if response.status_code != 200:
        print(f"Failed to fetch page, status: {response.status_code}", file=sys.stderr)
        return None
        
    html = response.text
    
    # Try to find ytInitialPlayerResponse
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        # Try another variation
        match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
    
    if not match:
        print("Failed to find ytInitialPlayerResponse in page source.", file=sys.stderr)
        # Write HTML to inspect if needed
        # Path("scratch/error.html").write_text(html, encoding="utf-8")
        return None
        
    try:
        player_response = json.loads(match.group(1))
    except Exception as e:
        print(f"Failed to parse player response JSON: {e}", file=sys.stderr)
        return None
        
    captions = player_response.get("captions", {})
    tracklist = captions.get("playerCaptionsTracklistRenderer", {})
    caption_tracks = tracklist.get("captionTracks", [])
    
    return caption_tracks

def fetch_and_format_transcript(track_url, output_path):
    print(f"Fetching transcript XML from {track_url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(track_url, headers=headers, impersonate="chrome120")
    if response.status_code != 200:
        print(f"Failed to fetch transcript XML, status: {response.status_code}", file=sys.stderr)
        return False
        
    xml_content = response.text
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"Failed to parse transcript XML: {e}", file=sys.stderr)
        # Maybe it's JSON format?
        try:
            js = json.loads(xml_content)
            # handle JSON if it is returned
            # JSON format usually has events
            # For simplicity, let's log the first 200 chars
            print(f"Response is not XML. Start of response: {xml_content[:200]}")
        except:
            pass
        return False
        
    raw_lines = []
    for text_elem in root.findall('text'):
        text = text_elem.text
        if not text:
            # Might be empty or contain children like <b>
            text = "".join(text_elem.itertext())
        text = text.strip().replace('\n', ' ')
        
        start_str = text_elem.attrib.get('start', '0')
        try:
            start = float(start_str)
        except ValueError:
            start = 0.0
            
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        
        raw_lines.append(f"{timestamp} {text}")
        
    if not raw_lines:
        print("No text segments found in XML.", file=sys.stderr)
        return False
        
    output_path.write_text("\n".join(raw_lines), encoding="utf-8")
    print(f"Successfully wrote {len(raw_lines)} lines to {output_path}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_transcript.py <video_id>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    caption_tracks = extract_caption_tracks(video_id)
    if not caption_tracks:
        print("No caption tracks found.", file=sys.stderr)
        sys.exit(1)
        
    print("Available Caption Tracks:")
    for track in caption_tracks:
        print(f"- {track.get('languageCode')} ({track.get('name', {}).get('simpleText')}) - URL: {track.get('baseUrl')[:50]}...")
        
    # Search for Spanish first
    selected_track = None
    for track in caption_tracks:
        if track.get('languageCode') == 'es':
            selected_track = track
            print("Selected Spanish track.")
            break
            
    if not selected_track:
        # Search for English
        for track in caption_tracks:
            if track.get('languageCode') == 'en':
                selected_track = track
                print("Selected English track.")
                break
                
    if not selected_track:
        # Select first track
        selected_track = caption_tracks[0]
        print(f"Selected first available track ({selected_track.get('languageCode')}).")
        
    track_url = selected_track.get('baseUrl')
    if not track_url:
        print("Selected track has no baseUrl.", file=sys.stderr)
        sys.exit(1)
        
    # Make sure we get format vtt or ttml (baseUrl by default usually returns XML format)
    vault_root = Path(__file__).parent.parent
    output_file = vault_root / "scratch" / "raw_transcript.txt"
    
    success = fetch_and_format_transcript(track_url, output_file)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
