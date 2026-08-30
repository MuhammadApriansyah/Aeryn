from fastapi import APIRouter

router = APIRouter()

# Dashboard HTML routes
from apps.api.routers.dashboard_html import router as dashboard_html_router
router.include_router(dashboard_html_router)

