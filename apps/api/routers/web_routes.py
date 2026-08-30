"""V61.0 — Web routes router for Aeryn API."""
from fastapi import APIRouter, RedirectResponse
from fastapi.responses import FileResponse, HTMLResponse
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

router = APIRouter()


