"""V61.4 — Web routes for Aeryn Dashboard."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
import os

router = APIRouter()
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMPLATE = os.path.join(BASE, "apps", "web", "templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    p = os.path.join(TEMPLATE, "dashboard.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return "<h1>Aeryn</h1>"

@router.get("/favicon.ico")
async def favicon():
    return HTMLResponse("")
