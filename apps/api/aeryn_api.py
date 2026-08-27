#!/usr/bin/env python3
"""V39.64 — Aeryn API Service: FastAPI wrapper for Aeryn core."""

import os
import sys
import time
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aeryn_core.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning_style import needs_research, COGNITIVE_CHAIN_OF_THOUGHT_RULE
from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.social_memory import SocialMemory
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.graph_memory import get_graph_memory
from aeryn_core.persona_engine import load_persona
from aeryn_core.config import ensure_dirs, DATABASE_DIR

app = FastAPI(title="Aeryn API", version="39.64")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ──────────────────────────────────────

class RunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: str = "default"
    context: dict = {}

class RunResponse(BaseModel):
    session_id: str
    status: str  # "ok" | "blocked" | "error"
    safety: dict
    adapter: Optional[str]
    needs_research: bool
    prompt: str
    response: str
    fallback: str = ""
    trace: list = []

class HealthResponse(BaseModel):
    status: str
    uptime: float
    memory_mb: float
    safety_engine: bool
    vault: bool
    search: bool
    version: str = "39.64"

# ── State ────────────────────────────────────────────────────────

_start_time = time.time()
_request_count = 0
_error_count = 0

# ── Middleware ────────────────────────────────────────────────────

@app.middleware("http")
async def track_requests(request: Request, call_next):
    global _request_count, _error_count
    _request_count += 1
    try:
        response = await call_next(request)
        return response
    except Exception:
        _error_count += 1
        raise

# ── Endpoints ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    import psutil
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    
    safety_ok = get_safety_engine() is not None
    vault_ok = AerynVault() is not None
    search_ok = get_search_engine() is not None
    
    status = "healthy" if all([safety_ok, vault_ok, search_ok]) else "degraded"
    
    return HealthResponse(
        status=status,
        uptime=round(time.time() - _start_time, 1),
        memory_mb=round(mem_mb, 1),
        safety_engine=safety_ok,
        vault=vault_ok,
        search=search_ok,
    )

@app.get("/status")
async def status():
    """Service status."""
    return {
        "status": "running",
        "uptime": round(time.time() - _start_time, 1),
        "requests": _request_count,
        "errors": _error_count,
        "error_rate": round(_error_count / max(_request_count, 1) * 100, 2),
    }

@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    """Run goal through Aeryn pipeline."""
    session_id = req.session_id
    goal = req.goal
    trace = []
    
    # Stage 1: Safety
    eng = get_safety_engine()
    safety_result = eng.check_input(goal)
    trace.append({"stage": "safety", "status": "blocked" if not safety_result.safe else "pass"})
    
    if not safety_result.safe:
        return RunResponse(
            session_id=session_id,
            status="blocked",
            safety=safety_result.to_dict(),
            adapter=None,
            needs_research=False,
            prompt="",
            response=f"Request blocked: {safety_result.reason}",
            fallback=safety_result.fallback,
            trace=trace,
        )
    
    # Stage 2: Research detection
    research = needs_research(goal)
    trace.append({"stage": "research", "detected": research})
    
    # Stage 3: Adapter selection
    adapter = get_active_adapter(goal)
    adapter_name = adapter.name if adapter else None
    trace.append({"stage": "adapter", "selected": adapter_name})
    
    # Stage 4: Prompt compilation
    persona = load_persona()
    prompt_parts = []
    prompt_parts.append(f"SYSTEM: {persona[:500]}")
    if research:
        prompt_parts.append("RESEARCH: Web search needed")
    if adapter:
        ctx = render_adapter_context(goal)
        if ctx:
            prompt_parts.append(f"ADAPTER: {ctx}")
    prompt_parts.append(f"USER: {goal}")
    prompt = "\n".join(prompt_parts)
    trace.append({"stage": "prompt", "length": len(prompt)})
    
    # Stage 5: Simulated LLM response (replace with actual LLM call)
    response = f"Aeryn processing: {goal[:100]}"
    if adapter:
        response += f"\nUsing adapter: {adapter_name}"
    if research:
        response += "\n[Research phase would query web]"
    response += "\n\n[LLM response would appear here in production]"
    
    # Stage 6: Output validation
    clean = sanitize_output(response)
    output_valid = "sk-" not in clean
    trace.append({"stage": "output", "valid": output_valid})
    
    return RunResponse(
        session_id=session_id,
        status="ok",
        safety=safety_result.to_dict(),
        adapter=adapter_name,
        needs_research=research,
        prompt=prompt[:200] + "...",
        response=clean[:500],
        trace=trace,
    )

@app.get("/search")
async def search(q: str, limit: int = 10):
    """Search memories."""
    hse = get_search_engine()
    results = hse.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/vault/list")
async def vault_list(layer: str = "Wiki"):
    """List vault entries."""
    vault = AerynVault()
    entries = vault.search("", layer=layer, limit=50)
    return {"layer": layer, "entries": entries, "count": len(entries)}

@app.post("/vault/write")
async def vault_write(title: str, body: str, layer: str = "Wiki", tags: str = ""):
    """Write to vault."""
    vault = AerynVault()
    entry = VaultEntry(
        layer=layer,
        title=title,
        body=body,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    path = vault.write(entry)
    return {"status": "ok", "path": path}

@app.get("/social/{user_id}")
async def social_get(user_id: str):
    """Get social memory for user."""
    sm = SocialMemory()
    facts = sm.get_facts(user_id)
    return {"user_id": user_id, "facts": facts, "count": len(facts)}

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3001, log_level="info")
