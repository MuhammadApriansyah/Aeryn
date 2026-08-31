"""V61.0 — Web routes router for Aeryn API."""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse, JSONResponse
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

router = APIRouter()

# SPA root — serve dashboard HTML
@router.get("/", response_class=HTMLResponse)
async def spa_root():
    """Serve dashboard HTML for client-side routing pages."""
    from apps.web.server import _serve_dashboard
    return _serve_dashboard()

# Redirect all old SPA routes to single dashboard
for _route in ["/projects", "/workspaces", "/chat", "/audit", "/settings", "/notifications"]:
    def make_redirect():
        async def redirect():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/")
        return redirect
    _handler = make_redirect()
    _handler.__name__ = f"redirect_{_route.strip('/')}"
    router.add_api_route(_route, endpoint=_handler)

@router.get("/app/{spa:path}", response_class=HTMLResponse)
async def spa_fallback(spa: str):
    """Serve dashboard HTML for client-side routing routes."""
    SPA_ROUTES = {"/", "/projects", "/workspaces", "/chat", "/plugins", "/audit", "/settings", "/notifications"}
    from apps.web.server import _serve_dashboard
    if "/" + spa in SPA_ROUTES:
        return _serve_dashboard()
    return JSONResponse({"error": "Not found"}, status_code=404)
