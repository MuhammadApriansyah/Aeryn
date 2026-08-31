"""V61.2 — Web routes for Aeryn Dashboard."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter()
# Go up to project root: apps/api/routers/web_routes.py -> /home/sen/aeryn-core-agent
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMPLATE = os.path.join(BASE, "apps", "web", "templates")
STATIC = os.path.join(BASE, "apps", "web", "static")

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    p = os.path.join(TEMPLATE, "dashboard.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return "<h1>Aeryn</h1>"

@router.get("/static/css/{f:path}")
async def css(f: str):
    fp = os.path.join(STATIC, "css", f)
    if os.path.exists(fp):
        return FileResponse(fp)
    return HTMLResponse("/* not found */", status_code=404)

@router.get("/static/js/{f:path}")
async def js(f: str):
    fp = os.path.join(STATIC, "js", f)
    if os.path.exists(fp):
        return FileResponse(fp)
    return HTMLResponse("// not found", status_code=404)

@router.get("/favicon.ico")
async def favicon():
    p = os.path.join(TEMPLATE, "favicon.html")
    if os.path.exists(p):
        return FileResponse(p, media_type="text/html")
    return HTMLResponse("")
