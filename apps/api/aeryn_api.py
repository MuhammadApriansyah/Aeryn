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
from aeryn_core.config import ensure_dirs

app = FastAPI(title="Aeryn Daemon", version="39.64")

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

@app.get("/dashboard")
async def dashboard():
    """Serve monitoring dashboard HTML."""
    return Response(
        content=DASHBOARD_HTML,
        media_type="text/html",
    )

@app.get("/dashboard/stats")
async def dashboard_stats():
    """Get statistics for dashboard."""
    try:
        # Read memory from /proc/meminfo (works in proon)
        mem_total = 0
        mem_available = 0
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])
        except Exception:
            pass
        
        mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
        mem_total_mb = mem_total / 1024 if mem_total else 0
        mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0
        
        # Disk
        import shutil
        disk = shutil.disk_usage("/")
        
        # Process memory
        process_mem = 0
        try:
            with open(f"/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        process_mem = int(line.split()[1]) / 1024
                        break
        except Exception:
            pass
        
        # Vault stats
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


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aeryn Dashboard</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; padding: 20px; }
  h1 { font-size: 24px; margin-bottom: 8px; color: #00ff88; }
  .subtitle { color: #666; margin-bottom: 24px; font-size: 14px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: #12121a; border: 1px solid #222; border-radius: 12px; padding: 20px; }
  .card h3 { font-size: 12px; text-transform: uppercase; color: #888; margin-bottom: 8px; }
  .card .value { font-size: 28px; font-weight: bold; color: #00ff88; }
  .card .sub { font-size: 12px; color: #666; margin-top: 4px; }
  .section { background: #12121a; border: 1px solid #222; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  .section h2 { font-size: 16px; margin-bottom: 12px; color: #00ccff; }
  .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .online { background: #00ff88; box-shadow: 0 0 6px #00ff88; }
  .offline { background: #ff4444; }
  .refresh { float: right; background: #1a1a2e; border: 1px solid #333; color: #00ff88; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .refresh:hover { background: #222; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #222; }
  th { color: #888; font-weight: 600; }
  .progress { height: 6px; background: #1a1a2e; border-radius: 3px; overflow: hidden; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #00ff88, #00ccff); transition: width 0.3s; }
</style>
</head>
<body>
<h1>🚀 Aeryn Dashboard</h1>
<p class="subtitle">Real-time monitoring — v39.64</p>

<button class="refresh" onclick="loadStats()">🔄 Refresh</button>

<div class="grid" id="cards">
  <div class="card"><h3>CPU</h3><div class="value" id="cpu">--</div><div class="sub"><div class="progress"><div class="progress-fill" id="cpu-bar"></div></div></div></div>
  <div class="card"><h3>Memory</h3><div class="value" id="mem">--</div><div class="sub" id="mem-sub">--</div></div>
  <div class="card"><h3>Disk Free</h3><div class="value" id="disk">--</div><div class="sub" id="disk-sub">-- used</div></div>
  <div class="card"><h3>Process</h3><div class="value" id="proc-mem">--</div><div class="sub" id="uptime">-- uptime</div></div>
</div>

<div class="section">
  <h2>🧠 Aeryn Stats</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Vault Entries</td><td id="vault-total">--</td></tr>
    <tr><td>Search Documents</td><td id="search-docs">--</td></tr>
    <tr><td>Social People</td><td id="social-ppl">--</td></tr>
    <tr><td>Total Requests</td><td id="req-total">--</td></tr>
    <tr><td>Errors</td><td id="err-total">--</td></tr>
    <tr><td>Safety Engine</td><td><span class="status-dot online"></span>OK</td></tr>
  </table>
</div>

<div class="section">
  <h2>📁 Vault Layers</h2>
  <table id="vault-table"><tr><th>Layer</th><th>Entries</th></tr></table>
</div>

<script>
async function loadStats() {
  try {
    const r = await fetch('/dashboard/stats');
    const d = await r.json();
    
    if (d.error) { document.body.innerHTML = '<h1>Error: '+d.error+'</h1>'; return; }
    
    const s = d.system, a = d.aeryn;
    
    document.getElementById('cpu').textContent = s.cpu_percent + '%';
    document.getElementById('cpu-bar').style.width = s.cpu_percent + '%';
    document.getElementById('mem').textContent = s.memory_used_mb + ' MB';
    document.getElementById('mem-sub').textContent = s.memory_percent + '% used';
    document.getElementById('disk').textContent = s.disk_free_gb + ' GB';
    document.getElementById('disk-sub').textContent = s.disk_percent + '% used';
    document.getElementById('proc-mem').textContent = s.process_mem_mb + ' MB';
    document.getElementById('uptime').textContent = Math.round(s.uptime_s / 60) + 'm uptime';
    
    document.getElementById('vault-total').textContent = a.vault_total_entries;
    document.getElementById('search-docs').textContent = a.search_docs;
    document.getElementById('social-ppl').textContent = a.social_people;
    document.getElementById('req-total').textContent = a.requests_total;
    document.getElementById('err-total').textContent = a.errors_total;
    
    const table = document.getElementById('vault-table');
    table.innerHTML = '<tr><th>Layer</th><th>Entries</th></tr>';
    for (const [layer, count] of Object.entries(a.vault_layers)) {
      table.innerHTML += '<tr><td>' + layer + '</td><td>' + count + '</td></tr>';
    }
  } catch(e) {
    document.body.innerHTML = '<h1>Connection failed: ' + e.message + '</h1>';
  }
}

loadStats();
setInterval(loadStats, 30000); // refresh every 30s
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
