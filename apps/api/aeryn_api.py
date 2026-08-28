#!/usr/bin/env python3
"""V40.44 — Aeryn Daemon :3010 — Full Feature Set."""

import os, sys, time, json, uuid, sqlite3
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request
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
from aeryn_core.multi_agent import get_multi_agent_orchestrator, AgentRole, TaskPriority as AgentTaskPriority
from aeryn_core.memory_decay import get_memory_decay_engine
from aeryn_core.entity_resolution import get_entity_resolver
from aeryn_core.owasp_security import get_owasp_security
from aeryn_core.plugin_system import get_plugin_manager
from aeryn_core.long_horizon import get_long_horizon_planner, TaskPriority
from aeryn_core.temporal_memory import get_temporal_memory
from aeryn_core.self_improvement import get_self_improvement_engine
from aeryn_core.skill_crystallization import get_skill_crystallizer
from aeryn_core.cloud_sync import get_cloud_sync
from aeryn_core.constitutional_ai import get_constitutional_ai
from aeryn_core.emotional_intelligence import get_emotional_intelligence
from aeryn_core.telegram_bot import get_telegram_bot
from aeryn_core.email_agent import get_email_agent
from aeryn_core.calendar_integration import get_calendar
from aeryn_core.github_integration import get_github
from aeryn_core.data_encryption import get_encryption
from aeryn_core.auth_manager import get_auth

app = FastAPI(title="Aeryn Daemon", version="40.52")

_start_time = time.time()
_request_count = 0
_error_count = 0

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

@app.get("/health")
async def health():
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "40.44"}
    except ImportError:
        return {"status": "healthy", "version": "40.44"}

@app.post("/compile")
async def compile(req: CompileRequest):
    eng = get_safety_engine()
    safety = eng.check_input(req.user_prompt)
    research = needs_research(req.user_prompt)
    adapter = get_active_adapter(req.user_prompt)
    persona = load_persona()
    emotional_tensor = {"safety_risk": safety.risk, "needs_research": research, "adapter": adapter.name if adapter else None, "safe": safety.safe}
    sm = SocialMemory()
    facts = sm.get_facts(req.session_id)
    prompt_parts = []
    if req.base_prompt: prompt_parts.append(req.base_prompt[:500])
    prompt_parts.append(f"\n[User: {req.user_prompt}]")
    if facts: prompt_parts.append(f"\n[Context: {', '.join(str(f) for f in facts[:5])}]")
    if adapter:
        ctx = render_adapter_context(req.user_prompt)
        if ctx: prompt_parts.append(f"\n{ctx}")
    gate_mode = "blocked" if not safety.safe else ("research" if research else ("adapter" if adapter else "standard"))
    return {"ok": True, "gate_mode": gate_mode, "blackboard": {"emotional_tensor_snapshot": emotional_tensor}, "memories": facts[:10] if facts else [], "compiled_prompt": "\n".join(prompt_parts), "safety": safety.to_dict()}

@app.post("/digest")
async def digest(req: DigestRequest):
    eng = get_safety_engine()
    clean_response = sanitize_output(req.response)
    vault = AerynVault()
    if len(req.user_prompt) > 10 and len(clean_response) > 10:
        try:
            vault.write(VaultEntry(layer=LAYER_WIKI, title=f"Conversation {req.session_id[:8]}", body=f"User: {req.user_prompt[:200]}\n\nResponse: {clean_response[:500]}", tags=["conversation", "auto"]))
        except Exception: pass
    return {"ok": True, "status": "digested", "accounting_ledger_audit": {"audit_payload": {"session_id": req.session_id, "timestamp": time.time()}}, "cog_mem_lifecycle_telemetry": {"focus_segment_retained": len(req.user_prompt) > 10}}

@app.post("/run")
async def run(req: RunRequest):
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    if not safety.safe: return {"status": "blocked", "safety": safety.to_dict()}
    research = needs_research(req.goal)
    adapter = get_active_adapter(req.goal)
    persona = load_persona()
    prompt = f"{persona}\n\nUser: {req.goal}"
    if adapter: prompt += f"\n{render_adapter_context(req.goal)}"
    response = f"Processing: {req.goal[:200]}"
    if adapter: response += f"\n[Adapter: {adapter.name}]"
    if research: response += "\n[Research needed]"
    return {"status": "ok", "session_id": req.session_id, "safety": safety.to_dict(), "adapter": adapter.name if adapter else None, "needs_research": research, "response": sanitize_output(response)}

@app.get("/search")
async def search(q: str, limit: int = 10):
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
<p class="subtitle">Real-time monitoring — v40.54</p>

<button class="refresh" onclick="loadStats()">🔄 Refresh</button>

<div class="grid" id="cards">
  <div class="card"><h3>Memory</h3><div class="value" id="mem">--</div><div class="sub" id="mem-sub">--</div></div>
  <div class="card"><h3>Disk Free</h3><div class="value" id="disk">--</div><div class="sub" id="disk-sub">-- used</div></div>
  <div class="card"><h3>Process</h3><div class="value" id="proc-mem">--</div><div class="sub" id="uptime">-- uptime</div></div>
  <div class="card"><h3>Requests</h3><div class="value" id="req-total">--</div><div class="sub" id="err-total">-- errors</div></div>
</div>

<div class="section">
  <h2>🧠 Aeryn Stats</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Vault Entries</td><td id="vault-total">--</td></tr>
    <tr><td>Search Documents</td><td id="search-docs">--</td></tr>
    <tr><td>Social People</td><td id="social-ppl">--</td></tr>
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
    
    document.getElementById('mem').textContent = s.memory_used_mb + ' MB';
    document.getElementById('mem-sub').textContent = s.memory_percent + '% used';
    document.getElementById('disk').textContent = s.disk_free_gb + ' GB';
    document.getElementById('disk-sub').textContent = s.disk_percent + '% used';
    document.getElementById('proc-mem').textContent = s.process_mem_mb + ' MB';
    document.getElementById('uptime').textContent = Math.round(s.uptime_s / 60) + 'm uptime';
    document.getElementById('req-total').textContent = a.requests_total;
    document.getElementById('err-total').textContent = a.errors_total + ' errors';
    
    document.getElementById('vault-total').textContent = a.vault_total_entries;
    document.getElementById('search-docs').textContent = a.search_docs;
    document.getElementById('social-ppl').textContent = a.social_people;
    
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
setInterval(loadStats, 30000);
</script>
</body>
</html>"""

@app.get("/dashboard/stats")
async def dashboard_stats():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = mem_available = 0
        for line in lines:
            if line.startswith("MemTotal:"): mem_total = int(line.split()[1])
            elif line.startswith("MemAvailable:"): mem_available = int(line.split()[1])
        mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
        mem_total_mb = mem_total / 1024 if mem_total else 0
        mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0
        import shutil
        disk = shutil.disk_usage("/")
        process_mem = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"): process_mem = int(line.split()[1]) / 1024; break
        except Exception: pass
        vault = AerynVault()
        vault_counts = vault.count_entries()
        total_vault = sum(vault_counts.values())
        hse = get_search_engine()
        doc_count = hse._doc_count if hasattr(hse, '_doc_count') else 0
        sm = SocialMemory()
        person_count = len(sm._data.get("people", {})) if hasattr(sm, '_data') else 0
        return {"timestamp": time.time(), "system": {"memory_total_mb": round(mem_total_mb, 1), "memory_used_mb": round(mem_used_mb, 1), "memory_percent": mem_pct, "disk_free_gb": round(disk.free / (1024**3), 2), "disk_percent": round((disk.total - disk.free) / disk.total * 100, 1), "process_mem_mb": round(process_mem, 1), "uptime_s": round(time.time() - _start_time, 0)}, "aeryn": {"vault_total_entries": total_vault, "vault_layers": vault_counts, "search_docs": doc_count, "social_people": person_count, "requests_total": _request_count, "errors_total": _error_count, "safety_engine": True}}
    except Exception as e:
        return {"error": str(e)}

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

@app.post("/dream/synthesize")
async def dream_synthesize(user_id: str = "default", days: int = 7):
    synthesizer = get_dream_synthesizer()
    return synthesizer.synthesize(user_id, days)

@app.get("/dream/insights")
async def get_dream_insights(user_id: str = "default", limit: int = 20):
    synthesizer = get_dream_synthesizer()
    return synthesizer.get_insights(user_id, limit)

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

@app.get("/guardrails/validators")
async def list_validators(category: str = None):
    guardrails = get_enhanced_guardrails()
    if category: return {"validators": guardrails.get_validators_by_category(category)}
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

@app.post("/agents/register")
async def register_agent(name: str, role: str = "worker", capabilities: str = "[]"):
    orchestrator = get_multi_agent_orchestrator()
    caps = json.loads(capabilities) if capabilities.startswith("[") else []
    try: agent_role = AgentRole(role)
    except ValueError: agent_role = AgentRole.WORKER
    agent_id = orchestrator.register_agent(name, agent_role, caps)
    return {"agent_id": agent_id, "status": "registered"}

@app.get("/agents")
async def list_agents():
    orchestrator = get_multi_agent_orchestrator()
    return {"agents": orchestrator.get_active_agents()}

@app.post("/agents/tasks/create")
async def create_agent_task(title: str, description: str = "", assigned_to: str = None, assigned_by: str = None, priority: int = 5):
    orchestrator = get_multi_agent_orchestrator()
    try: task_priority = AgentTaskPriority(priority)
    except ValueError: task_priority = AgentTaskPriority.MEDIUM
    task_id = orchestrator.create_task(title, description, assigned_to, assigned_by, task_priority)
    return {"task_id": task_id, "status": "created"}

@app.get("/agents/tasks")
async def list_agent_tasks(status: str = None):
    orchestrator = get_multi_agent_orchestrator()
    return {"tasks": orchestrator.get_tasks(status=status)}

@app.post("/memory/decay")
async def run_decay(user_id: str = "default"):
    engine = get_memory_decay_engine()
    return engine.decay_all(user_id)

@app.get("/memory/decay/stats")
async def get_decay_stats():
    engine = get_memory_decay_engine()
    return engine.get_decay_stats()

@app.post("/memory/entities/register")
async def register_entity(name: str, entity_type: str, properties: str = "{}"):
    resolver = get_entity_resolver()
    props = json.loads(properties)
    entity_id = resolver.register_entity(name, entity_type, props)
    return {"entity_id": entity_id}

@app.get("/memory/entities/resolve")
async def resolve_entity(name: str, entity_type: str = None):
    resolver = get_entity_resolver()
    result = resolver.resolve(name, entity_type)
    return {"entity": result}

@app.get("/memory/entities")
async def list_entities(entity_type: str = None):
    resolver = get_entity_resolver()
    return {"entities": resolver.get_all_entities(entity_type)}

@app.post("/plugins/install")
async def install_plugin(source_dir: str):
    manager = get_plugin_manager()
    plugin = manager.install_plugin(source_dir)
    if plugin: return {"status": "installed", "plugin": plugin.name}
    return {"status": "error", "error": "Failed to install plugin"}

@app.get("/plugins")
async def list_plugins():
    manager = get_plugin_manager()
    return {"plugins": manager.list_plugins()}

@app.delete("/plugins/{name}")
async def uninstall_plugin(name: str):
    manager = get_plugin_manager()
    if manager.uninstall_plugin(name): return {"status": "uninstalled"}
    return {"status": "error", "error": "Plugin not found"}

@app.post("/security/scan")
async def security_scan(text: str, context: str = "general"):
    security = get_owasp_security()
    return security.scan(text, context)

@app.get("/security/controls")
async def list_controls():
    security = get_owasp_security()
    return {"controls": list(security._controls.keys())}

@app.get("/discord/commands")
async def discord_commands():
    from aeryn_core.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    return {"commands": handler.get_commands()}

@app.post("/discord/interaction")
async def discord_interaction(interaction: dict):
    from aeryn_core.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    result = await handler.handle_interaction(interaction)
    return result

@app.post("/planning/tasks/create")
async def create_plan(title: str, description: str = "", priority: int = 5):
    planner = get_long_horizon_planner()
    try: task_priority = TaskPriority(priority)
    except ValueError: task_priority = TaskPriority.MEDIUM
    task_id = planner.create_task(title, description, task_priority)
    return {"task_id": task_id}

@app.post("/planning/tasks/{task_id}/decompose")
async def decompose_task(task_id: str, subtasks: list):
    planner = get_long_horizon_planner()
    subtask_ids = planner.decompose_task(task_id, subtasks)
    return {"subtask_ids": subtask_ids}

@app.post("/planning/tasks/{task_id}/execute")
async def execute_plan(task_id: str):
    planner = get_long_horizon_planner()
    result = planner.execute_task(task_id)
    return result

@app.get("/planning/tasks/{task_id}")
async def get_task(task_id: str):
    planner = get_long_horizon_planner()
    task = planner.get_task(task_id)
    subtasks = planner.get_subtasks(task_id)
    return {"task": task, "subtasks": subtasks}

@app.get("/planning/tasks")
async def list_plans(status: str = None):
    planner = get_long_horizon_planner()
    return {"tasks": planner.get_all_tasks(status)}

@app.post("/temporal/store")
async def store_temporal(user_id: str, memory_type: str, title: str, content: str, timestamp: str = None):
    temporal = get_temporal_memory()
    mem_id = temporal.store(user_id, memory_type, title, content, timestamp)
    return {"memory_id": mem_id}

@app.get("/temporal/query")
async def temporal_query(user_id: str, query: str):
    temporal = get_temporal_memory()
    return temporal.query_time(user_id, query)

@app.get("/temporal/timeline/{user_id}")
async def get_timeline(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"timeline": temporal.get_timeline(user_id, days)}

@app.get("/temporal/trends/{user_id}")
async def get_trends(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"trends": temporal.detect_trends(user_id, days)}

@app.post("/improvement/feedback")
async def submit_feedback(user_id: str, interaction_type: str, input_text: str, output_text: str, rating: int = None, feedback_text: str = ""):
    engine = get_self_improvement_engine()
    fid = engine.feedback.record_interaction(user_id, interaction_type, input_text, output_text)
    if rating is not None: engine.feedback.submit_feedback(fid, rating, feedback_text)
    return {"feedback_id": fid, "status": "recorded"}

@app.get("/improvement/report")
async def get_improvement_report(user_id: str = "default"):
    engine = get_self_improvement_engine()
    return engine.get_improvement_report(user_id)

@app.post("/skills/detect-patterns")
async def detect_patterns(user_id: str = "default", min_frequency: int = 3):
    crystallizer = get_skill_crystallizer()
    patterns = crystallizer.detector.get_frequent_patterns(user_id, min_frequency)
    return {"patterns": patterns}

@app.post("/skills/crystallize")
async def crystallize_skill(user_id: str, pattern_id: str, skill_name: str, description: str = ""):
    crystallizer = get_skill_crystallizer()
    skill_id = crystallizer.crystallize(user_id, pattern_id, skill_name, description)
    return {"skill_id": skill_id}

@app.get("/skills")
async def list_skills(active_only: bool = True):
    crystallizer = get_skill_crystallizer()
    return {"skills": crystallizer.get_skills(active_only=active_only)}

@app.post("/sync/backup")
async def create_backup(backup_name: str = None):
    sync = get_cloud_sync()
    return sync.create_backup(backup_name)

@app.get("/sync/backups")
async def list_backups():
    sync = get_cloud_sync()
    return {"backups": sync.list_backups()}

@app.post("/sync/restore")
async def restore_backup(backup_name: str, dry_run: bool = False):
    sync = get_cloud_sync()
    return sync.restore_backup(backup_name, dry_run)

@app.get("/constitutional/principles")
async def get_principles():
    cai = get_constitutional_ai()
    conn = sqlite3.connect(cai.db_path)
    rows = conn.execute("SELECT id, name, description, priority FROM principles WHERE is_active=1 ORDER BY priority DESC").fetchall()
    conn.close()
    return {"principles": [{"id": r[0], "name": r[1], "description": r[2], "priority": r[3]} for r in rows]}

@app.post("/constitutional/check")
async def constitutional_check(action: str, context: str = ""):
    cai = get_constitutional_ai()
    return cai.check_action(action, context)

@app.post("/emotion/detect")
async def detect_emotion(text: str, user_id: str = "default"):
    ei = get_emotional_intelligence()
    result = ei.detect_mood(text)
    ei.record_mood(user_id, text)
    result["empathy_response"] = ei.get_empathy_response(result["mood"])
    return result

@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    bot = get_telegram_bot()
    return bot.handle_update(update)

@app.get("/telegram/commands")
async def telegram_commands():
    bot = get_telegram_bot()
    return {"commands": bot.get_commands()}

@app.post("/email/triage")
async def email_triage(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return agent.triage_email(sender, subject, body)

@app.post("/email/generate-reply")
async def email_reply(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return {"reply": agent.generate_reply(sender, subject, body)}

@app.post("/calendar/events")
async def create_event(user_id: str, title: str, start_time: str, end_time: str = None, description: str = "", location: str = ""):
    cal = get_calendar()
    event_id = cal.create_event(user_id, title, start_time, end_time, description, location)
    return {"event_id": event_id}

@app.get("/calendar/events/{user_id}")
async def get_events(user_id: str, start: str = None, end: str = None):
    cal = get_calendar()
    return {"events": cal.get_events(user_id, start, end)}

@app.get("/github/status")
async def github_status():
    gh = get_github()
    return {"status": "ready", "token": "configured" if gh.token else "not set"}

@app.post("/encrypt")
async def encrypt_data(data: str):
    enc = get_encryption()
    return {"encrypted": enc.encrypt(data)}

@app.post("/decrypt")
async def decrypt_data(encrypted_data: str):
    enc = get_encryption()
    return {"decrypted": enc.decrypt(encrypted_data)}

@app.post("/auth/register")
async def register_user(username: str, password: str, role: str = "user"):
    auth = get_auth()
    user_id = auth.create_user(username, password, role)
    return {"user_id": user_id, "status": "created"}

@app.post("/auth/login")
async def login(username: str, password: str):
    auth = get_auth()
    token = auth.authenticate(username, password)
    return {"token": token, "status": "success" if token else "failed"}

@app.get("/metrics")
async def get_metrics():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return monitor.get_metrics()

@app.get("/alerts")
async def get_alerts():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return {"alerts": monitor.get_alerts()}


# ── Browser Automation ──────────────────────────────────────────

@app.post("/browser/task")
async def browser_task(url: str, actions: list, user_id: str = "default"):
    from aeryn_core.browser_vector import get_browser
    browser = get_browser()
    return browser.run_task(url, actions, user_id)

# ── Vector DB ──────────────────────────────────────────────────

@app.post("/vectordb/collections")
async def create_collection(name: str, dimension: int = 384, description: str = ""):
    from aeryn_core.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"collection": vdb.create_collection(name, dimension, description)}

@app.post("/vectordb/{collection}/add")
async def add_vectors(collection: str, texts: list, embeddings: list = None, metadatas: list = None):
    from aeryn_core.browser_vector import get_vector_db
    vdb = get_vector_db()
    ids = vdb.add(collection, texts, embeddings, metadatas)
    return {"ids": ids}

@app.post("/vectordb/{collection}/search")
async def search_vectors(collection: str, query_embedding: list, limit: int = 5):
    from aeryn_core.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"results": vdb.search(collection, query_embedding, limit)}

@app.delete("/vectordb/{collection}")
async def delete_collection(collection: str):
    from aeryn_core.browser_vector import get_vector_db
    vdb = get_vector_db()
    vdb.delete_collection(collection)
    return {"status": "deleted"}

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
