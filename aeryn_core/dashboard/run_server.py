#!/usr/bin/env python3
"""Run the dashboard server as a standalone script."""
import http.server
import socketserver
import json
import os
import sys
import signal
import time

PORT = int(os.environ.get("AERYN_DASHBOARD_PORT", 3020))
HOST = os.environ.get("AERYN_DASHBOARD_HOST", "127.0.0.1")

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aeryn Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #00d9ff; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
        .card h2 { margin-bottom: 16px; color: #00d9ff; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
        .project-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; }
        .btn { display: inline-block; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s; border: none; font-size: 14px; }
        .btn-primary { background: #00d9ff; color: #1a1a2e; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
        .status.online { background: rgba(0,255,136,0.1); color: #00ff88; }
        .log-console { background: #0d1117; border-radius: 8px; padding: 16px; font-family: 'Courier New', monospace; font-size: 13px; max-height: 300px; overflow-y: auto; color: #58a6ff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">Aeryn Dashboard</div>
            <div style="color:rgba(255,255,255,0.5);">''' + str(PORT) + '''</div>
        </header>
        
        <div class="card">
            <h2>Projects</h2>
            <div class="grid">
                <div class="project-card">
                    <h3>Welcome</h3>
                    <p>Your project will appear here</p>
                    <span class="status online">Online</span>
                    <div style="margin-top:12px;"><button class="btn btn-primary">View</button></div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Logs</h2>
            <div class="log-console">
                <div>[INFO] Dashboard started</div>
                <div>[OK] Ready</div>
            </div>
        </div>
    </div>
</body>
</html>'''

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode())
    
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"Dashboard running at http://{HOST}:{PORT}")
        httpd.serve_forever()
