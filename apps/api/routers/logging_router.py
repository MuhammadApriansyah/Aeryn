"""V61.1 — Observability: request-log stats & recent (fitur Hermes)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/logging/stats")
async def logging_stats(window_hours: int = 24):
    """Ringkasan observability: total, error-rate, latency, slowest, top-errors."""
    from aeryn_core.advanced_monitoring.request_logger import get_request_logger
    return get_request_logger().stats(window_hours=window_hours)


@router.get("/logging/recent")
async def logging_recent(limit: int = 40):
    """Request terakhir (method, path, status, duration, ts)."""
    from aeryn_core.advanced_monitoring.request_logger import get_request_logger
    return {"logs": get_request_logger().recent(limit=limit)}