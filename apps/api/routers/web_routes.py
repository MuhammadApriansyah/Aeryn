"""V61.5 — Web routes for Aeryn Dashboard (React SPA)."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter()

# React app paths
REACT_DIST = "/home/sen/aeryn-core-agent/apps/web-vite/dist"
REACT_INDEX = os.path.join(REACT_DIST, "index.html")
REACT_STATIC = os.path.join(REACT_DIST, "static")


@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve React SPA."""
    if os.path.exists(REACT_INDEX):
        with open(REACT_INDEX, encoding="utf-8") as f:
            return f.read()
    return "<h1>Aeryn</h1>"


@router.get("/static/{path:path}")
async def static_files(path: str):
    """Serve static files from React dist."""
    react_file = os.path.join(REACT_STATIC, path)
    if os.path.exists(react_file):
        return FileResponse(react_file)
    return HTMLResponse("Not found", status_code=404)


@router.get("/favicon.ico")
async def favicon():
    return HTMLResponse("")
