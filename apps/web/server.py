#!/usr/bin/env python3
"""Dashboard Web Server — Serve HTML/CSS/JS dashboard."""
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter()

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
TEMPLATE_DIR = os.path.join(DASHBOARD_DIR, "templates")
STATIC_DIR = os.path.join(DASHBOARD_DIR, "static")

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    template_path = os.path.join(TEMPLATE_DIR, "dashboard.html")
    if os.path.exists(template_path):
        with open(template_path) as f:
            return f.read()
    return "<h1>Aeryn Dashboard</h1><p>Template not found</p>"

@router.get("/static/css/{filename}")
async def css(filename: str):
    file_path = os.path.join(STATIC_DIR, "css", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Not found"}

@router.get("/static/js/{filename}")
async def js(filename: str):
    file_path = os.path.join(STATIC_DIR, "js", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Not found"}
