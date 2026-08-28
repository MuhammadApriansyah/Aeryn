#!/usr/bin/env python3
"""V40.0 — Aeryn Daemon :3010 (Hermes-compatible) — Production Ready."""

import os
import sys
import time
import json
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from aeryn_core.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning_style import needs_research
from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.social_memory import SocialMemory
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.persona_engine import load_persona
from aeryn_core.shared_db import get_shared_db
from aeryn_core.config import ensure_dirs
from aeryn_core.dream_synthesis import get_dream_synthesizer
from aeryn_core.enhanced_memory import get_entity_extractor, get_preference_learner, get_cross_session_recall
from aeryn_core.enhanced_guardrails import get_enhanced_guardrails
from aeryn_core.enhanced_sandbox import get_enhanced_sandbox, SandboxLimits

app = FastAPI(title="Aeryn Daemon", version="40.0")

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
        return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "40.0"}
    except ImportError:
        return {"status": "healthy", "version": "40.0"}

@app.post("/compile")
async def compile(req: CompileRequest):
    """Compile cognitive context (Hermes plugin: aeryn_context)."""
    eng = get_safety_engine()
    safety = eng.check_input(req.user_prompt)
    research = needs_research(req.user_prompt)
    adapter = get_active_adapter(req.user_prompt)
    adapter_name = adapter.name if adapter else None
    persona = load_persona()
    
    emotional_tensor = {
        "safety_risk": safety.risk,
        "needs_research": research,
        "adapter": adapter_name,
        "safe": safety.safe,
    }
    
    sm = SocialMemory()
    facts = sm.get_facts(req.session_id)
    
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
        "blackboard": {"emotional_tensor_snapshot": emotional_tensor},
        "memories": facts[:10] if facts else [],
        "compiled_prompt": compiled_prompt,
        "safety": safety.to_dict(),
    }

@app.post("/digest")
async def digest(req: DigestRequest):
    """Report final response (Hermes plugin: aeryn_digest)."""
    eng = get_safety_engine()
    clean_response = sanitize_output(req.response)
    vault = AerynVault()
    
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
            pass
    
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
        "accounting_ledger_audit": {"audit_payload": audit},
        "cog_mem_lifecycle_telemetry": {"focus_segment_retained": len(req.user_prompt) > 10},
    }

@app.post("/run")
async def run(req: RunRequest):
    """Run goal through Aeryn pipeline."""
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

@app.get("/dashboard/stats")
async def dashboard_stats():
    """Get statistics for dashboard."""
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = 0
        mem_available = 0
        for line in lines:
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                mem_available = int(line.split()[1])
        
        mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
        mem_total_mb = mem_total / 1024 if mem_total else 0
        mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0
        
        import shutil
        disk = shutil.disk_usage("/")
        
        process_mem = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        process_mem = int(line.split()[1]) / 1024
                        break
        except Exception:
            pass
        
        vault = AerynVault()
        vault_counts = vault.count_entries()
        total_vault = sum(vault_counts.values())
        
        hse = get_search_engine()
        doc_count = hse._doc_count if hasattr(hse, '_doc_count') else 0
        
        sm = SocialMemory()
        person_count = len(sm._data.get("people", {})) if hasattr(sm, '_data') else 0
        
        return {
            "timestamp": time.time(),
            "system": {
                "memory_total_mb": round(mem_total_mb, 1),
                "memory_used_mb": round(mem_used_mb, 1),
                "memory_percent": mem_pct,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.total - disk.free) / disk.total * 100, 1),
                "process_mem_mb": round(process_mem, 1),
                "uptime_s": round(time.time() - _start_time, 0),
            },
            "aeryn": {
                "vault_total_entries": total_vault,
                "vault_layers": vault_counts,
                "search_docs": doc_count,
                "social_people": person_count,
                "requests_total": _request_count,
                "errors_total": _error_count,
                "safety_engine": True,
            },
        }
    except Exception as e:
        return {"error": str(e)}

# ── Shared DB Endpoints ─────────────────────────────────────────

@app.get("/shared/reminders/due")
async def get_due_reminders():
    db = get_shared_db()
    reminders = db.get_due_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@app.get("/shared/reminders")
async def get_all_reminders():
    db = get_shared_db()
    reminders = db.get_all_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@app.post("/shared/reminders/add")
async def add_reminder(text: str, when: str, source: str = "n8n", target: str = "all"):
    db = get_shared_db()
    rid = db.add_reminder(text, when, source, target)
    return {"id": rid, "status": "ok"}

@app.post("/shared/reminders/mark-sent")
async def mark_reminder_sent(reminder_id: str):
    db = get_shared_db()
    db.mark_reminder_sent(reminder_id)
    return {"status": "ok"}

@app.get("/shared/tasks")
async def get_pending_tasks():
    db = get_shared_db()
    tasks = db.get_pending_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@app.post("/shared/tasks/add")
async def add_task(title: str, description: str = "", priority: int = 5):
    db = get_shared_db()
    tid = db.add_task(title, description, priority)
    return {"id": tid, "status": "ok"}

@app.post("/shared/tasks/update")
async def update_task(task_id: str, status: str = None, progress: float = None, result: str = None, error: str = None):
    db = get_shared_db()
    db.update_task(task_id, status, progress, result, error)
    return {"status": "ok"}

@app.get("/shared/daily-log")
async def get_daily_log():
    db = get_shared_db()
    return db.get_or_create_daily_log()

@app.post("/shared/daily-log/update")
async def update_daily_log(date: str = None, **kwargs):
    db = get_shared_db()
    db.update_daily_log(date, **kwargs)
    return {"status": "ok"}

@app.get("/shared/stats")
async def get_stats():
    db = get_shared_db()
    return db.get_stats()

# ── Dream Synthesis ─────────────────────────────────────────────

@app.post("/dream/synthesize")
async def dream_synthesize(user_id: str = "default", days: int = 7):
    synthesizer = get_dream_synthesizer()
    return synthesizer.synthesize(user_id, days)

@app.get("/dream/insights")
async def get_dream_insights(user_id: str = "default", limit: int = 20):
    synthesizer = get_dream_synthesizer()
    return synthesizer.get_insights(user_id, limit)

# ── Enhanced Memory ─────────────────────────────────────────────

@app.post("/memory/extract-entities")
async def extract_entities(text: str):
    extractor = get_entity_extractor()
    return extractor.extract(text)

@app.post("/memory/preference/learn")
async def learn_preference(user_id: str, category: str, key: str, value: str, confidence: float = 0.5):
    learner = get_preference_learner()
    learner.learn(user_id, category, key, value, confidence)
    return {"status": "ok"}

@app.get("/memory/preferences/{user_id}")
async def get_preferences(user_id: str, min_confidence: float = 0.0):
    learner = get_preference_learner()
    return learner.get_preferences(user_id, min_confidence)

# ── Enhanced Guardrails ─────────────────────────────────────────

@app.get("/guardrails/validators")
async def list_validators(category: str = None):
    guardrails = get_enhanced_guardrails()
    if category:
        return {"validators": guardrails.get_validators_by_category(category)}
    return {"validators": guardrails.get_all_validators()}

@app.post("/guardrails/validate-input")
async def validate_input(text: str = None, context: str = "general", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        context = body.get("context", "general")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_input(text, context)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "fallback": result.fallback}

@app.post("/guardrails/validate-output")
async def validate_output(text: str = None, expected_format: str = "text", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        expected_format = body.get("expected_format", "text")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_output(text, expected_format)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "sanitized": result.sanitized, "fallback": result.fallback}

# ── Enhanced Sandbox ────────────────────────────────────────────

@app.post("/sandbox/create")
async def create_sandbox(user_id: str = "default", allow_network: bool = False, max_time: int = 30):
    sandbox = get_enhanced_sandbox()
    limits = SandboxLimits(max_execution_time=max_time, allow_network=allow_network)
    session_id = sandbox.create_session(user_id=user_id, limits=limits)
    return {"session_id": session_id, "status": "created"}

@app.post("/sandbox/execute")
async def sandbox_execute(session_id: str, command: str, user_id: str = "default"):
    sandbox = get_enhanced_sandbox()
    return sandbox.execute(session_id, command, user_id)

@app.get("/sandbox/session/{session_id}")
async def get_sandbox_session(session_id: str):
    sandbox = get_enhanced_sandbox()
    info = sandbox.get_session_info(session_id)
    history = sandbox.audit.get_session_history(session_id)
    return {"info": info, "history": history}

@app.delete("/sandbox/session/{session_id}")
async def cleanup_sandbox(session_id: str):
    sandbox = get_enhanced_sandbox()
    sandbox.cleanup_session(session_id)
    return {"status": "cleaned"}

# ── Monitoring (Production) ─────────────────────────────────────

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return monitor.get_metrics()

@app.get("/alerts")
async def get_alerts():
    """Active alerts."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return {"alerts": monitor.get_alerts()}

# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
