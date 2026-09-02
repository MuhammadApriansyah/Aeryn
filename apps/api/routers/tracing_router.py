"""Observability Router — trace & span endpoints for agent telemetry."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/v1/traces", tags=["observability"])


@router.get("/")
async def list_traces(limit: int = 20):
    """List recent traces."""
    from aeryn_core.observability.tracing import get_trace_collector
    collector = get_trace_collector()
    traces = collector.list_traces(limit)
    return {"traces": traces, "count": len(traces)}


@router.get("/{trace_id}")
async def get_trace(trace_id: str):
    """Get full trace with all spans."""
    from aeryn_core.observability.tracing import get_trace_collector
    collector = get_trace_collector()
    spans = collector.get_trace(trace_id)
    if not spans:
        raise HTTPException(status_code=404, detail="Trace not found")

    total_tokens = collector.get_token_total(trace_id)
    return {
        "trace_id": trace_id,
        "spans": [s.to_dict() for s in spans],
        "span_count": len(spans),
        "total_tokens": total_tokens,
    }


@router.get("/{trace_id}/tokens")
async def get_trace_tokens(trace_id: str):
    """Get token usage for a trace."""
    from aeryn_core.observability.tracing import get_trace_collector
    collector = get_trace_collector()
    total_tokens = collector.get_token_total(trace_id)
    return {"trace_id": trace_id, "total_tokens": total_tokens}