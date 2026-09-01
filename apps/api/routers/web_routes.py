"""V61.5 — Web routes for Aeryn Dashboard (React + esbuild)."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter()
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Prefer React app (esbuild dist), fallback to old dashboard
REACT_DIST = os.path.join(BASE, "apps", "web-vite", "dist")
REACT_INDEX = os.path.join(REACT_DIST, "index.html")
REACT_STATIC = os.path.join(REACT_DIST, "static")
OLD_TEMPLATE = os.path.join(BASE, "apps", "web", "templates", "dashboard.html")

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve React app if built, else fallback to old dashboard."""
    import os
    REACT_INDEX = "/home/sen/aeryn-core-agent/apps/web-vite/dist/index.html"
    OLD_TEMPLATE = "/home/sen/aeryn-core-agent/apps/web/templates/dashboard.html"
    
    if os.path.exists(REACT_INDEX):
        with open(REACT_INDEX, encoding="utf-8") as f:
            return f.read()
    elif os.path.exists(OLD_TEMPLATE):
        with open(OLD_TEMPLATE, encoding="utf-8") as f:
            return f.read()
    return "<h1>Aeryn</h1>"

@router.get("/static/{path:path}")
async def static_files(path: str):
    """Serve static files from React dist or old static dir."""
    # Try React dist first
    react_file = os.path.join(REACT_STATIC, path)
    if os.path.exists(react_file):
        return FileResponse(react_file)
    
    # Fallback to old static
    old_file = os.path.join(BASE, "apps", "web", "static", path)
    if os.path.exists(old_file):
        return FileResponse(old_file)
    
    return HTMLResponse("Not found", status_code=404)

@router.get("/favicon.ico")
async def favicon():
    return HTMLResponse("")
