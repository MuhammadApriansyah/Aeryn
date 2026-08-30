#!/usr/bin/env python3
"""Dashboard Server — Web-based UI for project management."""
import http.server
import socketserver
import json
import os
import threading
from typing import Dict, Optional

PORT = 3020

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
        .nav { display: flex; gap: 20px; }
        .nav a { color: rgba(255,255,255,0.7); text-decoration: none; padding: 10px 20px; border-radius: 8px; transition: all 0.3s; }
        .nav a:hover, .nav a.active { background: rgba(0,217,255,0.1); color: #00d9ff; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 20px; backdrop-filter: blur(10px); }
        .card h2 { margin-bottom: 16px; color: #00d9ff; font-size: 18px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
        .project-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; transition: all 0.3s; cursor: pointer; }
        .project-card:hover { transform: translateY(-4px); border-color: #00d9ff; box-shadow: 0 10px 30px rgba(0,217,255,0.1); }
        .project-card h3 { margin-bottom: 8px; }
        .project-card p { color: rgba(255,255,255,0.5); font-size: 14px; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
        .status.online { background: rgba(0,255,136,0.1); color: #00ff88; }
        .status.offline { background: rgba(255,100,100,0.1); color: #ff6464; }
        .btn { display: inline-block; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s; border: none; font-size: 14px; }
        .btn-primary { background: #00d9ff; color: #1a1a2e; }
        .btn-primary:hover { background: #00b8d4; transform: translateY(-2px); }
        .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; }
        .btn-secondary:hover { background: rgba(255,255,255,0.2); }
        .log-console { background: #0d1117; border-radius: 8px; padding: 16px; font-family: 'Courier New', monospace; font-size: 13px; max-height: 300px; overflow-y: auto; color: #58a6ff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🤖 Aeryn</div>
            <nav class="nav">
                <a href="javascript:showTab('projects')" class="active">Projects</a>
                <a href="javascript:showTab('create')">Create</a>
                <a href="javascript:showTab('logs')">Logs</a>
                <a href="javascript:showTab('settings')">Settings</a>
            </nav>
        </header>
        
        <div id="projects" class="tab-content">
            <div class="card">
                <h2>📁 My Projects</h2>
                <div class="grid" id="project-list">
                    <div class="project-card">
                        <h3>my-app</h3>
                        <p>React + Fastify + SQLite</p>
                        <span class="status online">Online</span>
                        <div style="margin-top:12px; display:flex; gap:8px;">
                            <button class="btn btn-primary">Start</button>
                            <button class="btn btn-secondary">Stop</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="create" class="tab-content" style="display:none">
            <div class="card">
                <h2>✨ Create New Project</h2>
                <div style="margin-bottom:16px;">
                    <label style="display:block; margin-bottom:8px; color:rgba(255,255,255,0.7);">Project Name</label>
                    <input type="text" placeholder="my-app" style="width:100%; padding:12px 16px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:#fff;">
                </div>
                <div style="margin-bottom:16px;">
                    <label style="display:block; margin-bottom:8px; color:rgba(255,255,255,0.7);">Type</label>
                    <select style="width:100%; padding:12px 16px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:#fff;">
                        <option>Web App (React + Fastify)</option>
                        <option>API Only</option>
                        <option>Discord Bot</option>
                    </select>
                </div>
                <button class="btn btn-primary">Create Project</button>
            </div>
        </div>
        
        <div id="logs" class="tab-content" style="display:none">
            <div class="card">
                <h2>📋 Server Logs</h2>
                <div class="log-console">
                    <div>[INFO] Server started on port 3020</div>
                    <div>[OK] Dashboard ready</div>
                </div>
            </div>
        </div>
        
        <div id="settings" class="tab-content" style="display:none">
            <div class="card">
                <h2>⚙️ Settings</h2>
                <div style="margin-bottom:16px;">
                    <label style="display:block; margin-bottom:8px; color:rgba(255,255,255,0.7);">Default Port</label>
                    <input type="number" value="3010" style="width:100%; padding:12px 16px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:#fff;">
                </div>
                <button class="btn btn-primary">Save Settings</button>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
            document.getElementById(tab).style.display = 'block';
        }
    </script>
</body>
</html>'''

class DashboardServer:
    def __init__(self, port=PORT):
        self.port = port
        self._server = None
        self._thread = None
    
    def start(self):
        handler = self._create_handler()
        self._server = socketserver.TCPServer(("", self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"Dashboard running at http://localhost:{self.port}")
    
    def stop(self):
        if self._server:
            self._server.shutdown()
    
    def _create_handler(self):
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
        
        return Handler

dashboard_server = DashboardServer()
