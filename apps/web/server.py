#!/usr/bin/env python3
"""Dashboard Web Server — SPA with real-time health and full page routing."""
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
TEMPLATE_DIR = os.path.join(DASHBOARD_DIR, "templates")
STATIC_DIR = os.path.join(DASHBOARD_DIR, "static")

# === STATIC FILES ===

@router.get("/static/css/{filename}")
async def css(filename: str):
    file_path = os.path.join(STATIC_DIR, "css", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "Not found"}, status_code=404)

@router.get("/static/js/{filename}")
async def js(filename: str):
    file_path = os.path.join(STATIC_DIR, "js", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "Not found"}, status_code=404)


# === PAGE ROUTES ===

@router.get("/", response_class=HTMLResponse)
async def home():
    return _serve_dashboard()

@router.get("/web", response_class=HTMLResponse)
async def web():
    return _serve_dashboard()

@router.get("/projects", response_class=HTMLResponse)
async def projects():
    return _serve_dashboard()

@router.get("/workspaces", response_class=HTMLResponse)
async def workspaces():
    return _serve_dashboard()

@router.get("/chat", response_class=HTMLResponse)
async def chat():
    return _serve_dashboard()

@router.get("/plugins", response_class=HTMLResponse)
async def plugins():
    return _serve_dashboard()

@router.get("/audit", response_class=HTMLResponse)
async def audit():
    return _serve_dashboard()

@router.get("/settings", response_class=HTMLResponse)
async def settings():
    return _serve_dashboard()


# === API PROXY ===

@router.get("/api/py/health")
async def health_proxy():
    """Proxy health check to main API."""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:3010/health")
        resp = urllib.request.urlopen(req, timeout=5)
        import json
        return JSONResponse(json.loads(resp.read()))
    except Exception:
        return JSONResponse({"status": "offline", "memory_mb": 0, "version": "--"})


@router.get("/api/py/adaptive/health")
async def adaptive_health_proxy():
    """Proxy adaptive health check to main API."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request("http://127.0.0.1:3010/api/adaptive/health")
        resp = urllib.request.urlopen(req, timeout=5)
        return JSONResponse(json.loads(resp.read()))
    except Exception:
        return JSONResponse({"status": "offline"})


@router.get("/api/py/adaptive/errors")
async def adaptive_errors_proxy():
    """Proxy adaptive errors check to main API."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request("http://127.0.0.1:3010/api/adaptive/errors")
        resp = urllib.request.urlopen(req, timeout=5)
        return JSONResponse(json.loads(resp.read()))
    except Exception:
        return JSONResponse({"total_errors": 0, "breakdown": []})


# === HELPER ===

def _serve_dashboard():
    template_path = os.path.join(TEMPLATE_DIR, "dashboard.html")
    if os.path.exists(template_path):
        with open(template_path) as f:
            return f.read()
    return "<h1>Aeryn Dashboard</h1>"
