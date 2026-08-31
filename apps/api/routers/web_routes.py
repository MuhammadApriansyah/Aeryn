"""V61.2 — Web routes router for Aeryn API (polished dashboard)."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import os

router = APIRouter()

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static")

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the polished dashboard."""
    template_path = os.path.join(TEMPLATE_DIR, "dashboard.html")
    if os.path.exists(template_path):
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>Aeryn Dashboard</h1><p>Template not found.</p>"

@router.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(TEMPLATE_DIR, "favicon.html"), media_type="text/html")
