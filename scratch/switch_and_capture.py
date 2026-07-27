import urllib.request
import json
import base64
import socket
import time

def main():
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    tv_tab = [t for t in tabs if 'tradingview.com/chart' in t.get('url','')][0]
    ws_url = tv_tab['webSocketDebuggerUrl']

    host = 'localhost'
    port = 9222
    path = ws_url.split(':9222')[1]

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    key = base64.b64encode(b'1234567890123456').decode('utf-8')
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.send(req.encode('utf-8'))
    s.recv(4096)

    mask = b'\x12\x34\x56\x78'
    def send_frame(data_bytes):
        m_payload = bytearray()
        for i, b in enumerate(data_bytes):
            m_payload.append(b ^ mask[i % 4])
        length = len(data_bytes)
        if length <= 125:
            header = bytearray([0x81, 0x80 | length])
        elif length <= 65535:
            header = bytearray([0x81, 0x80 | 126, (length >> 8) & 0xFF, length & 0xFF])
        else:
            header = bytearray([0x81, 0x80 | 127]) + length.to_bytes(8, 'big')
        s.send(header + mask + m_payload)

    # 1. Switch to CME_MINI:MNQ1! 1m
    js_script = """(function(){
        try {
            var api = window.TradingViewApi._activeChartWidgetWV.value();
            api.setSymbol('CME_MINI:MNQ1!');
            api.setResolution('1');
            return {success: true};
        } catch(e) {
            return {error: e.message};
        }
    })()"""

    cmd1 = json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': js_script}}).encode('utf-8')
    send_frame(cmd1)
    s.recv(65536)

    # Give TradingView time to reload the 1m MNQ chart
    time.sleep(3.0)

    # 2. Capture screenshot
    cmd2 = json.dumps({'id': 2, 'method': 'Page.captureScreenshot', 'params': {'format': 'png'}}).encode('utf-8')
    send_frame(cmd2)

    raw_data = bytearray()
    s.settimeout(3.0)
    while True:
        try:
            chunk = s.recv(65536)
            if not chunk: break
            raw_data.extend(chunk)
        except Exception:
            break
    s.close()

    txt = raw_data.decode('utf-8', errors='ignore')
    key_str = '"data":"'
    idx = txt.find(key_str)
    if idx != -1:
        end_idx = txt.find('"', idx + len(key_str))
        b64_str = txt[idx + len(key_str):end_idx]
        with open('imagenes/2026-07-27_chart.png', 'wb') as f:
            f.write(base64.b64decode(b64_str))
        print("OK: TradingView MNQ 1m chart captured successfully!")
    else:
        print("Error: Could not find screenshot payload")

if __name__ == "__main__":
    main()
