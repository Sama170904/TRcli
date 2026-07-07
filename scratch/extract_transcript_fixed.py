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
    proxies = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxies = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            print(f"Loaded {len(proxies)} proxies from ProxyScrape.")
    except Exception as e:
        print(f"Failed to fetch ProxyScrape list: {e}")
        
    # Also fetch from Github raw as fallback
    print("Fetching additional SOCKS5/HTTP proxies from GitHub list...")
    fallback_urls = [
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
    ]
    for url in fallback_urls:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                lines = [l.strip() for l in r.text.split('\n') if l.strip()]
                # filter IP:Port formats
                for l in lines:
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', l):
                        proxies.append(l)
        except Exception as e:
            print(f"Failed fallback {url}: {e}")
            
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for p in proxies:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
            
    print(f"Total unique proxies to try: {len(deduped)}")
    return deduped

def extract_caption_tracks_with_proxy(video_id, proxy_dict, headers):
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(
        url,
        headers=headers,
        impersonate="chrome120",
        proxies=proxy_dict,
        timeout=10
    )
    if response.status_code != 200:
        print(f"  Failed to fetch HTML page, status: {response.status_code}")
        return None
        
    html = response.text
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        match = re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
        
    if not match:
        print("  Failed to find ytInitialPlayerResponse in page source.")
        return None
        
    try:
        player_response = json.loads(match.group(1))
    except Exception as e:
        print(f"  Failed to parse player response JSON: {e}")
        return None
        
    captions = player_response.get("captions", {})
    tracklist = captions.get("playerCaptionsTracklistRenderer", {})
    caption_tracks = tracklist.get("captionTracks", [])
    
    return caption_tracks

def parse_and_save_xml(xml_content, output_path):
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"  Failed to parse transcript XML: {e}")
        # print first 100 chars of the content for debugging
        snippet = xml_content[:150].strip().replace('\n', ' ')
        print(f"  Response content snippet: {snippet}")
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
        print("  No text segments found in XML.")
        return False
        
    output_path.write_text("\n".join(raw_lines), encoding="utf-8")
    print(f"  Successfully wrote {len(raw_lines)} lines to {output_path}")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python scratch/extract_transcript_fixed.py <video_id> <output_filename_in_scratch>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    out_name = sys.argv[2]
    
    vault_root = Path(__file__).parent.parent
    output_file = vault_root / "scratch" / out_name
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    proxies = get_free_proxies()
    
    # Try direct first
    print("Trying direct connection first (HTML + XML)...")
    try:
        caption_tracks = extract_caption_tracks_with_proxy(video_id, None, headers)
        if caption_tracks:
            # Spanish first
            selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'es'), None)
            if not selected_track:
                selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'en'), None)
            if not selected_track:
                selected_track = caption_tracks[0]
                
            track_url = selected_track.get('baseUrl')
            print(f"  Direct connection got track: {selected_track.get('languageCode')}")
            response = requests.get(track_url, headers=headers, impersonate="chrome120", timeout=8)
            if response.status_code == 200:
                if parse_and_save_xml(response.text, output_file):
                    print("Direct connection succeeded!")
                    sys.exit(0)
    except Exception as e:
        print(f"Direct connection attempt failed: {e}")
        
    # If direct fails, loop through proxies
    for idx, proxy_ip in enumerate(proxies):
        print(f"[{idx+1}/{len(proxies)}] Trying proxy: {proxy_ip}...")
        proxy_dict = {
            "http": f"http://{proxy_ip}",
            "https": f"http://{proxy_ip}"
        }
        try:
            caption_tracks = extract_caption_tracks_with_proxy(video_id, proxy_dict, headers)
            if not caption_tracks:
                continue
                
            # Select language
            selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'es'), None)
            if not selected_track:
                selected_track = next((t for t in caption_tracks if t.get('languageCode') == 'en'), None)
            if not selected_track:
                selected_track = caption_tracks[0]
                
            track_url = selected_track.get('baseUrl')
            print(f"  Found track: {selected_track.get('languageCode')}. Fetching XML with same proxy...")
            
            response = requests.get(
                track_url,
                headers=headers,
                impersonate="chrome120",
                proxies=proxy_dict,
                timeout=10
            )
            
            if response.status_code == 200:
                if parse_and_save_xml(response.text, output_file):
                    print(f"Success with proxy {proxy_ip}!")
                    sys.exit(0)
            else:
                print(f"  XML request returned status code: {response.status_code}")
        except Exception as e:
            print(f"  Failed using proxy {proxy_ip}: {e}")
            
    print("All proxies failed to download transcript.", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()
