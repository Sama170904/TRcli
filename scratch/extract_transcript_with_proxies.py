import sys
import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from curl_cffi import requests

def get_free_proxies():
    print("Fetching free proxy list from ProxyScrape...")
    url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&skip_token=true&proxy_format=ipport&format=text&limit=30"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            print(f"Loaded {len(proxies)} proxies.")
            return proxies
    except Exception as e:
        print(f"Failed to fetch proxy list: {e}")
    return []

def extract_caption_tracks(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Fetching YouTube page for {video_id} (without proxy)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch page, status: {response.status_code}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error fetching page: {e}", file=sys.stderr)
        return None
        
    html = response.text
    
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
    
    if not match:
        print("Failed to find ytInitialPlayerResponse in page source.", file=sys.stderr)
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

def fetch_transcript_with_proxies(track_url, proxies, output_path):
    print("Attempting to download transcript XML using proxies...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # First try direct without proxy, just in case rate limit expired
    try:
        print("Trying direct connection first...")
        response = requests.get(track_url, headers=headers, impersonate="chrome120", timeout=5)
        if response.status_code == 200:
            if parse_and_save_xml(response.text, output_path):
                return True
    except Exception as e:
        print(f"Direct connection attempt failed: {e}")
        
    # Iterate through proxies
    for idx, proxy_ip_port in enumerate(proxies):
        print(f"[{idx+1}/{len(proxies)}] Trying proxy: {proxy_ip_port}...")
        proxy_dict = {
            "http": f"http://{proxy_ip_port}",
            "https": f"http://{proxy_ip_port}"
        }
        try:
            response = requests.get(
                track_url,
                headers=headers,
                impersonate="chrome120",
                proxies=proxy_dict,
                timeout=8
            )
            if response.status_code == 200:
                print(f"Success with proxy {proxy_ip_port}!")
                if parse_and_save_xml(response.text, output_path):
                    return True
            else:
                print(f"Proxy returned status code: {response.status_code}")
        except Exception as e:
            print(f"Proxy {proxy_ip_port} failed: {e}")
            
    print("All proxies failed.", file=sys.stderr)
    return False

def parse_and_save_xml(xml_content, output_path):
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"Failed to parse transcript XML: {e}", file=sys.stderr)
        return False
        
    raw_lines = []
    for text_elem in root.findall('text'):
        text = text_elem.text
        if not text:
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
    if len(sys.argv) < 3:
        print("Usage: python extract_transcript_with_proxies.py <video_id> <output_filename_in_scratch>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    out_name = sys.argv[2]
    
    vault_root = Path(__file__).parent.parent
    output_file = vault_root / "scratch" / out_name
    
    caption_tracks = extract_caption_tracks(video_id)
    if not caption_tracks:
        print("No caption tracks found.", file=sys.stderr)
        sys.exit(1)
        
    selected_track = None
    for track in caption_tracks:
        if track.get('languageCode') == 'es':
            selected_track = track
            print("Selected Spanish track.")
            break
            
    if not selected_track:
        for track in caption_tracks:
            if track.get('languageCode') == 'en':
                selected_track = track
                print("Selected English track.")
                break
                
    if not selected_track:
        selected_track = caption_tracks[0]
        print(f"Selected first available track ({selected_track.get('languageCode')}).")
        
    track_url = selected_track.get('baseUrl')
    if not track_url:
        print("Selected track has no baseUrl.", file=sys.stderr)
        sys.exit(1)
        
    proxies = get_free_proxies()
    if not proxies:
        print("No proxies available, trying direct download only...")
        proxies = []
        
    success = fetch_transcript_with_proxies(track_url, proxies, output_file)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
