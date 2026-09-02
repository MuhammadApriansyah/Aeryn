"""V61.5 — Web routes for Aeryn Dashboard (React SPA)."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter()

# React app paths
REACT_DIST = "/home/sen/aeryn-core-agent/apps/web-vite/dist"
REACT_INDEX = os.path.join(REACT_DIST, "index.html")
REACT_STATIC = os.path.join(REACT_DIST, "static")


@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Serve chat page."""
    chat_path = "/home/sen/aeryn-core-agent/apps/web/templates/chat.html"
    if os.path.exists(chat_path):
        with open(chat_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>Chat</h1>"


@router.get("/static/css/{path:path}")
async def css_files(path: str):
    """Serve CSS files."""
    css_file = os.path.join("/home/sen/aeryn-core-agent/apps/web/static/css", path)
    if os.path.exists(css_file):
        return FileResponse(css_file)
    return HTMLResponse("Not found", status_code=404)


@router.get("/static/js/{path:path}")
async def js_files(path: str):
    """Serve JS files."""
    js_file = os.path.join("/home/sen/aeryn-core-agent/apps/web/static/js", path)
    if os.path.exists(js_file):
        return FileResponse(js_file)
    return HTMLResponse("Not found", status_code=404)


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
