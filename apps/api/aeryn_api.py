#!/usr/bin/env python3
"""V39.64 — Aeryn Daemon :3010 (Hermes-compatible).

Endpoints matching hermes plugin expectations:
- GET  /health — health check
- POST /compile — compile cognitive context (called by aeryn_context tool)
- POST /digest  — report final response (called by aeryn_digest tool)
- POST /run     — run goal through Aeryn pipeline (standalone)
"""

import os
import sys
import time
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from aeryn_core.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning_style import needs_research
from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.social_memory import SocialMemory
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.persona_engine import load_persona
from aeryn_core.config import ensure_dirs

app = FastAPI(title="Aeryn Daemon", version="39.64")

# ── Request/Response Models ──────────────────────────────────────

class CompileRequest(BaseModel):
    session_id: str = "default"
    base_prompt: str = ""
    user_prompt: str = ""
    history: list = []
    tasks: list = []

class DigestRequest(BaseModel):
    session_id: str = "default"
    user_prompt: str = ""
    response: str = ""

class RunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])

# ── Endpoints ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check."""
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "39.64"}
    except ImportError:
        return {"status": "healthy", "version": "39.64"}

@app.post("/compile")
async def compile(req: CompileRequest):
    """Compile cognitive context (Hermes plugin: aeryn_context)."""
    eng = get_safety_engine()
    
    # Safety check on user prompt
    safety = eng.check_input(req.user_prompt)
    
    # Detect research
    research = needs_research(req.user_prompt)
    
    # Select adapter
    adapter = get_active_adapter(req.user_prompt)
    adapter_name = adapter.name if adapter else None
    
    # Build cognitive state
    persona = load_persona()
    
    emotional_tensor = {
        "safety_risk": safety.risk,
        "needs_research": research,
        "adapter": adapter_name,
        "safe": safety.safe,
    }
    
    # Get relevant memories from social memory
    sm = SocialMemory()
    facts = sm.get_facts(req.session_id)
    
    # Build compiled prompt
    prompt_parts = []
    if req.base_prompt:
        prompt_parts.append(req.base_prompt[:500])
    prompt_parts.append(f"\n[User: {req.user_prompt}]")
    
    if facts:
        prompt_parts.append(f"\n[Context: {', '.join(str(f) for f in facts[:5])}]")
    
    if adapter:
        ctx = render_adapter_context(req.user_prompt)
        if ctx:
            prompt_parts.append(f"\n{ctx}")
    
    compiled_prompt = "\n".join(prompt_parts)
    
    # Determine gate mode
    if not safety.safe:
        gate_mode = "blocked"
    elif research:
        gate_mode = "research"
    elif adapter:
        gate_mode = "adapter"
    else:
        gate_mode = "standard"
    
    return {
        "ok": True,
        "gate_mode": gate_mode,
        "blackboard": {
            "emotional_tensor_snapshot": emotional_tensor,
        },
        "memories": facts[:10] if facts else [],
        "compiled_prompt": compiled_prompt,
        "safety": safety.to_dict(),
    }

@app.post("/digest")
async def digest(req: DigestRequest):
    """Report final response (Hermes plugin: aeryn_digest)."""
    eng = get_safety_engine()
    
    # Sanitize output for any leaked secrets
    clean_response = sanitize_output(req.response)
    
    # Log the interaction (for memory consolidation)
    vault = AerynVault()
    
    # Store conversation entry if meaningful
    if len(req.user_prompt) > 10 and len(clean_response) > 10:
        try:
            entry = VaultEntry(
                layer=LAYER_WIKI,
                title=f"Conversation {req.session_id[:8]}",
                body=f"User: {req.user_prompt[:200]}\n\nResponse: {clean_response[:500]}",
                tags=["conversation", "auto"],
            )
            vault.write(entry)
        except Exception:
            pass  # Non-critical
    
    # Audit ledger
    audit = {
        "session_id": req.session_id,
        "timestamp": time.time(),
        "input_length": len(req.user_prompt),
        "output_length": len(clean_response),
        "sanitized": clean_response != req.response,
    }
    
    return {
        "ok": True,
        "status": "digested",
        "accounting_ledger_audit": {
            "audit_payload": audit,
        },
        "cog_mem_lifecycle_telemetry": {
            "focus_segment_retained": len(req.user_prompt) > 10,
        },
    }

@app.post("/run")
async def run(req: RunRequest):
    """Run goal through Aeryn pipeline (standalone)."""
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    
    if not safety.safe:
        return {"status": "blocked", "safety": safety.to_dict()}
    
    research = needs_research(req.goal)
    adapter = get_active_adapter(req.goal)
    
    persona = load_persona()
    prompt = f"{persona}\n\nUser: {req.goal}"
    if adapter:
        prompt += f"\n{render_adapter_context(req.goal)}"
    
    response = f"Processing: {req.goal[:200]}"
    if adapter:
        response += f"\n[Adapter: {adapter.name}]"
    if research:
        response += "\n[Research needed]"
    
    return {
        "status": "ok",
        "session_id": req.session_id,
        "safety": safety.to_dict(),
        "adapter": adapter.name if adapter else None,
        "needs_research": research,
        "response": sanitize_output(response),
    }

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

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
