#!/usr/bin/env python3
"""
V41.0 — Uptime Monitor.
Cek status API secara berkala.
"""
import os
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

os.chdir('/home/sen/aeryn-core-agent')

API_URL = os.environ.get('AERYN_API_URL', 'http://127.0.0.1:3010')
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'uptime.log')

def check_health():
    """Cek health endpoint."""
    try:
        req = urllib.request.Request(f'{API_URL}/health')
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        return True, data.get('version', 'unknown')
    except Exception as e:
        return False, str(e)

def log_status(online, message):
    """Log status ke file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f'{timestamp} | {"ONLINE" if online else "OFFLINE"} | {message}\n')

def main():
    """Main monitoring loop."""
    interval = int(os.environ.get('MONITOR_INTERVAL', '60'))  # default 60 detik
    
    print(f'Monitoring {API_URL} setiap {interval} detik...')
    
    while True:
        online, message = check_health()
        log_status(online, message)
        
        if not online:
            print(f'⚠️ OFFLINE: {message}')
        else:
            print(f'✅ ONLINE (v{message})')
        
        time.sleep(interval)

if __name__ == '__main__':
    main()
