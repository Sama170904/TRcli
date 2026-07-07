import sys
import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from curl_cffi import requests

def get_free_proxies():
    print("Fetching free proxy list from ProxyScrape...")
    url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&skip_token=true&proxy_format=ipport&format=text&limit=50"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            print(f"Loaded {len(proxies)} proxies.")
            return proxies
    except Exception as e:
        print(f"Failed to fetch proxy list: {e}")
    return []

def extract_caption_tracks_with_proxy(video_id, proxy_ip_port):
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    proxy_dict = {
        "http": f"http://{proxy_ip_port}",
        "https": f"http://{proxy_ip_port}"
    }
    
    response = requests.get(url, headers=headers, impersonate="chrome120", proxies=proxy_dict, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page, status: {response.status_code}")
        
    html = response.text
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
    
    if not match:
        raise Exception("Failed to find ytInitialPlayerResponse in page source.")
        
    player_response = json.loads(match.group(1))
    
    # Extract title too
    video_details = player_response.get("videoDetails", {})
    title = video_details.get("title", "Unknown Title")
    
    captions = player_response.get("captions", {})
    tracklist = captions.get("playerCaptionsTracklistRenderer", {})
    caption_tracks = tracklist.get("captionTracks", [])
    
    return title, caption_tracks

def fetch_and_format_transcript_with_proxy(track_url, proxy_ip_port, output_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    proxy_dict = {
        "http": f"http://{proxy_ip_port}",
        "https": f"http://{proxy_ip_port}"
    }
    response = requests.get(track_url, headers=headers, impersonate="chrome120", proxies=proxy_dict, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch transcript XML, status: {response.status_code}")
        
    xml_content = response.text
    root = ET.fromstring(xml_content)
    
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
        raise Exception("No text segments found in XML.")
        
    output_path.write_text("\n".join(raw_lines), encoding="utf-8")
    return len(raw_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scratch/extract_transcript_same_proxy.py <video_id>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    vault_root = Path(__file__).parent.parent
    output_file = vault_root / "scratch" / "raw_transcript.txt"
    
    proxies = get_free_proxies()
    if not proxies:
        print("No proxies loaded.")
        sys.exit(1)
        
    success = False
    for idx, proxy in enumerate(proxies):
        print(f"[{idx+1}/{len(proxies)}] Trying proxy: {proxy}...")
        try:
            title, caption_tracks = extract_caption_tracks_with_proxy(video_id, proxy)
            if not caption_tracks:
                print("No caption tracks found for this video using this proxy.")
                continue
                
            # Search for Spanish, then English
            selected_track = None
            for track in caption_tracks:
                if track.get('languageCode') == 'es':
                    selected_track = track
                    break
            if not selected_track:
                for track in caption_tracks:
                    if track.get('languageCode') == 'en':
                        selected_track = track
                        break
            if not selected_track:
                selected_track = caption_tracks[0]
                
            track_url = selected_track.get('baseUrl')
            if not track_url:
                continue
                
            line_count = fetch_and_format_transcript_with_proxy(track_url, proxy, output_file)
            print(f"SUCCESS! Title: {title}")
            print(f"Wrote {line_count} lines to {output_file}")
            
            # Write title to a temporary metadata file so the main script can read it
            (vault_root / "scratch" / "last_title.txt").write_text(title, encoding="utf-8")
            success = True
            break
        except Exception as e:
            print(f"Failed with proxy {proxy}: {e}")
            
    if not success:
        print("All proxies failed to retrieve transcript.")
        sys.exit(1)

if __name__ == '__main__':
    main()
