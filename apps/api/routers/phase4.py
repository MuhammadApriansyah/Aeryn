"""V61.0 — Phase 4 endpoints router for Aeryn API."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.platform.cloud_sync import get_cloud_sync
from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
from aeryn_core.adaptive import get_adaptive_system
from aeryn_core.platform.webhook_system import get_webhook_system
from aeryn_core.platform.email_agent import get_email_agent
from aeryn_core.platform.calendar_integration import get_calendar
from aeryn_core.platform.github_integration import get_github
from aeryn_core.utils.logger import info, warn, error
from aeryn_core.utils.performance import get_optimizer, get_uptime
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.platform.auto_task import get_auto_task
from aeryn_core.reasoning.proactive_engine import get_proactive_engine
from aeryn_core.reasoning.proactive_v2 import get_proactive_v2
from aeryn_core.memory.temporal_memory import get_temporal_memory

router = APIRouter()

# ── Phase 4 Endpoints ─────────────────────────

@router.get("/performance/stats")
async def performance_stats():
    """Get performance statistics."""
    opt = get_optimizer()
    return opt.get_system_stats()

@router.get("/uptime")
async def uptime():
    """Get uptime information."""
    ut = get_uptime()
    return {
        "uptime_s": ut.uptime_seconds,
        "uptime": ut.uptime_formatted,
        "restart_count": ut._restart_count,
    }

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check."""
    ut = get_uptime()
    return ut.health_check()

@router.get("/docs/swagger")
async def swagger_ui():
    """Serve Swagger UI."""
    from fastapi.openapi.docs import get_swagger_ui_html
    html = get_swagger_ui_html(openapi_url="/openapi.json", title="Aeryn API")
    return HTMLResponse(content=html.body.decode())

@router.get("/openapi.json")
async def openapi_schema():
    """Serve OpenAPI schema."""
    from fastapi.openapi.utils import get_openapi
    return get_openapi(
        title="Aeryn API",
        version="41.0",
        description="Aeryn Cognitive Agent Platform API",
        routes=router.routes,
    )

@router.get("/shared/daily-log")
async def get_daily_log():
    db = get_shared_db()
    return db.get_or_create_daily_log()

@router.post("/shared/daily-log/update")
async def update_daily_log(date: str = None, **kwargs):
    db = get_shared_db()
    db.update_daily_log(date, **kwargs)
    return {"status": "ok"}

@router.get("/shared/stats")
async def get_stats():
    db = get_shared_db()
    return db.get_stats()

@router.post("/dream/synthesize")
async def dream_synthesize(user_id: str = "default", days: int = 7):
    synthesizer = get_dream_synthesizer()
    return synthesizer.synthesize(user_id, days)

@router.get("/dream/insights")
async def get_dream_insights(user_id: str = "default", limit: int = 20):
    synthesizer = get_dream_synthesizer()
    return synthesizer.get_insights(user_id, limit)

@router.post("/memory/extract-entities")
async def extract_entities(text: str):
    extractor = get_entity_extractor()
    return extractor.extract(text)

@router.post("/memory/preference/learn")
async def learn_preference(user_id: str, category: str, key: str, value: str, confidence: float = 0.5):
    learner = get_preference_learner()
    learner.learn(user_id, category, key, value, confidence)
    return {"status": "ok"}

@router.get("/memory/preferences/{user_id}")
async def get_preferences(user_id: str, min_confidence: float = 0.0):
    learner = get_preference_learner()
    return learner.get_preferences(user_id, min_confidence)

@router.get("/guardrails/validators")
async def list_validators(category: str = None):
    guardrails = get_enhanced_guardrails()
    if category: return {"validators": guardrails.get_validators_by_category(category)}
    return {"validators": guardrails.get_all_validators()}

@router.post("/guardrails/validate-input")
async def validate_input(text: str = None, context: str = "general", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        context = body.get("context", "general")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_input(text, context)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "fallback": result.fallback}

@router.post("/guardrails/validate-output")
async def validate_output(text: str = None, expected_format: str = "text", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        expected_format = body.get("expected_format", "text")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_output(text, expected_format)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "sanitized": result.sanitized, "fallback": result.fallback}

@router.post("/sandbox/create")
async def create_sandbox(user_id: str = "default", allow_network: bool = False, max_time: int = 30):
    sandbox = get_enhanced_sandbox()
    limits = SandboxLimits(max_execution_time=max_time, allow_network=allow_network)
    session_id = sandbox.create_session(user_id=user_id, limits=limits)
    return {"session_id": session_id, "status": "created"}

@router.post("/sandbox/execute")
async def sandbox_execute(session_id: str, command: str, user_id: str = "default"):
    sandbox = get_enhanced_sandbox()
    return sandbox.execute(session_id, command, user_id)

@router.get("/sandbox/session/{session_id}")
async def get_sandbox_session(session_id: str):
    sandbox = get_enhanced_sandbox()
    info = sandbox.get_session_info(session_id)
    history = sandbox.audit.get_session_history(session_id)
    return {"info": info, "history": history}

@router.delete("/sandbox/session/{session_id}")
async def cleanup_sandbox(session_id: str):
    sandbox = get_enhanced_sandbox()
    sandbox.cleanup_session(session_id)
    return {"status": "cleaned"}

@router.post("/agents/register")
async def register_agent(name: str, role: str = "worker", capabilities: str = "[]"):
    orchestrator = get_multi_agent_orchestrator()
    caps = json.loads(capabilities) if capabilities.startswith("[") else []
    try: agent_role = AgentRole(role)
    except ValueError: agent_role = AgentRole.WORKER
    agent_id = orchestrator.register_agent(name, agent_role, caps)
    return {"agent_id": agent_id, "status": "registered"}

@router.get("/agents")
async def list_agents():
    orchestrator = get_multi_agent_orchestrator()
    return {"agents": orchestrator.get_active_agents()}

@router.post("/agents/tasks/create")
async def create_agent_task(title: str, description: str = "", assigned_to: str = None, assigned_by: str = None, priority: int = 5):
    orchestrator = get_multi_agent_orchestrator()
    try: task_priority = AgentTaskPriority(priority)
    except ValueError: task_priority = AgentTaskPriority.MEDIUM
    task_id = orchestrator.create_task(title, description, assigned_to, assigned_by, task_priority)
    return {"task_id": task_id, "status": "created"}

@router.get("/agents/tasks")
async def list_agent_tasks(status: str = None):
    orchestrator = get_multi_agent_orchestrator()
    return {"tasks": orchestrator.get_tasks(status=status)}

@router.post("/memory/decay")
async def run_decay(user_id: str = "default"):
    engine = get_memory_decay_engine()
    return engine.decay_all(user_id)

@router.get("/memory/decay/stats")
async def get_decay_stats():
    engine = get_memory_decay_engine()
    return engine.get_decay_stats()

@router.post("/memory/entities/register")
async def register_entity(name: str, entity_type: str, properties: str = "{}"):
    resolver = get_entity_resolver()
    props = json.loads(properties)
    entity_id = resolver.register_entity(name, entity_type, props)
    return {"entity_id": entity_id}

@router.get("/memory/entities/resolve")
async def resolve_entity(name: str, entity_type: str = None):
    resolver = get_entity_resolver()
    result = resolver.resolve(name, entity_type)
    return {"entity": result}

@router.get("/memory/entities")
async def list_entities(entity_type: str = None):
    resolver = get_entity_resolver()
    return {"entities": resolver.get_all_entities(entity_type)}

@router.post("/plugins/install")
async def install_plugin(source_dir: str):
    manager = get_plugin_manager()
    plugin = manager.install_plugin(source_dir)
    if plugin: return {"status": "installed", "plugin": plugin.name}
    return {"status": "error", "error": "Failed to install plugin"}

@router.get("/plugins/installed")
async def list_plugins():
    manager = get_plugin_manager()
    return {"plugins": manager.list_plugins()}

@router.delete("/plugins/{name}")
async def uninstall_plugin(name: str):
    manager = get_plugin_manager()
    if manager.uninstall_plugin(name): return {"status": "uninstalled"}
    return {"status": "error", "error": "Plugin not found"}

@router.post("/security/scan")
async def security_scan(text: str, context: str = "general"):
    security = get_owasp_security()
    return security.scan(text, context)

@router.get("/security/controls")
async def list_controls():
    security = get_owasp_security()
    return {"controls": list(security._controls.keys())}

@router.get("/discord/commands")
async def discord_commands():
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    return {"commands": handler.get_commands()}

@router.post("/discord/interaction")
async def discord_interaction(interaction: dict):
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    result = await handler.handle_interaction(interaction)
    return result

@router.post("/planning/tasks/create")
async def create_plan(title: str, description: str = "", priority: int = 5):
    planner = get_long_horizon_planner()
    try: task_priority = TaskPriority(priority)
    except ValueError: task_priority = TaskPriority.MEDIUM
    task_id = planner.create_task(title, description, task_priority)
    return {"task_id": task_id}

@router.post("/planning/tasks/{task_id}/decompose")
async def decompose_task(task_id: str, subtasks: list):
    planner = get_long_horizon_planner()
    subtask_ids = planner.decompose_task(task_id, subtasks)
    return {"subtask_ids": subtask_ids}

@router.post("/planning/tasks/{task_id}/execute")
async def execute_plan(task_id: str):
    planner = get_long_horizon_planner()
    result = planner.execute_task(task_id)
    return result

@router.get("/planning/tasks/{task_id}")
async def get_task(task_id: str):
    planner = get_long_horizon_planner()
    task = planner.get_task(task_id)
    subtasks = planner.get_subtasks(task_id)
    return {"task": task, "subtasks": subtasks}

@router.get("/planning/tasks")
async def list_plans(status: str = None):
    planner = get_long_horizon_planner()
    return {"tasks": planner.get_all_tasks(status)}

@router.post("/temporal/store")
async def store_temporal(user_id: str, memory_type: str, title: str, content: str, timestamp: str = None):
    temporal = get_temporal_memory()
    mem_id = temporal.store(user_id, memory_type, title, content, timestamp)
    return {"memory_id": mem_id}

@router.get("/temporal/query")
async def temporal_query(user_id: str, query: str):
    temporal = get_temporal_memory()
    return temporal.query_time(user_id, query)

@router.get("/temporal/timeline/{user_id}")
async def get_timeline(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"timeline": temporal.get_timeline(user_id, days)}

@router.get("/temporal/trends/{user_id}")
async def get_trends(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"trends": temporal.detect_trends(user_id, days)}

@router.post("/improvement/feedback")
async def submit_feedback(user_id: str, interaction_type: str, input_text: str, output_text: str, rating: int = None, feedback_text: str = ""):
    engine = get_self_improvement_engine()
    fid = engine.feedback.record_interaction(user_id, interaction_type, input_text, output_text)
    if rating is not None: engine.feedback.submit_feedback(fid, rating, feedback_text)
    return {"feedback_id": fid, "status": "recorded"}

@router.get("/improvement/report")
async def get_improvement_report(user_id: str = "default"):
    engine = get_self_improvement_engine()
    return engine.get_improvement_report(user_id)

@router.post("/skills/detect-patterns")
async def detect_patterns(user_id: str = "default", min_frequency: int = 3):
    crystallizer = get_skill_crystallizer()
    patterns = crystallizer.detector.get_frequent_patterns(user_id, min_frequency)
    return {"patterns": patterns}

@router.post("/skills/crystallize")
async def crystallize_skill(user_id: str, pattern_id: str, skill_name: str, description: str = ""):
    crystallizer = get_skill_crystallizer()
    skill_id = crystallizer.crystallize(user_id, pattern_id, skill_name, description)
    return {"skill_id": skill_id}

@router.get("/skills")
async def list_skills(active_only: bool = True):
    crystallizer = get_skill_crystallizer()
    return {"skills": crystallizer.get_skills(active_only=active_only)}

@router.post("/sync/backup")
async def create_backup(backup_name: str = None):
    sync = get_cloud_sync()
    return sync.create_backup(backup_name)

@router.get("/sync/backups")
async def list_backups():
    sync = get_cloud_sync()
    return {"backups": sync.list_backups()}

@router.post("/sync/restore")
async def restore_backup(backup_name: str, dry_run: bool = False):
    sync = get_cloud_sync()
    return sync.restore_backup(backup_name, dry_run)

@router.get("/constitutional/principles")
async def get_principles():
    cai = get_constitutional_ai()
    conn = sqlite3.connect(cai.db_path)
    rows = conn.execute("SELECT id, name, description, priority FROM principles WHERE is_active=1 ORDER BY priority DESC").fetchall()
    conn.close()
    return {"principles": [{"id": r[0], "name": r[1], "description": r[2], "priority": r[3]} for r in rows]}

@router.post("/constitutional/check")
async def constitutional_check(action: str, context: str = ""):
    cai = get_constitutional_ai()
    return cai.check_action(action, context)

@router.post("/emotion/detect")
async def detect_emotion(text: str, user_id: str = "default"):
    ei = get_emotional_intelligence()
    result = ei.detect_mood(text)
    ei.record_mood(user_id, text)
    result["empathy_response"] = ei.get_empathy_response(result["mood"])
    return result

@router.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    bot = get_telegram_bot()
    return bot.handle_update(update)

@router.get("/telegram/commands")
async def telegram_commands():
    bot = get_telegram_bot()
    return {"commands": bot.get_commands()}

@router.post("/email/triage")
async def email_triage(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return agent.triage_email(sender, subject, body)

@router.post("/email/generate-reply")
async def email_reply(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return {"reply": agent.generate_reply(sender, subject, body)}

@router.post("/calendar/events")
async def create_event(user_id: str, title: str, start_time: str, end_time: str = None, description: str = "", location: str = ""):
    cal = get_calendar()
    event_id = cal.create_event(user_id, title, start_time, end_time, description, location)
    return {"event_id": event_id}

@router.get("/calendar/events/{user_id}")
async def get_events(user_id: str, start: str = None, end: str = None):
    cal = get_calendar()
    return {"events": cal.get_events(user_id, start, end)}

@router.get("/github/status")
async def github_status():
    gh = get_github()
    return {"status": "ready", "token": "configured" if gh.token else "not set"}

@router.post("/encrypt")
async def encrypt_data(data: str):
    enc = get_encryption()
    return {"encrypted": enc.encrypt(data)}

@router.post("/decrypt")
async def decrypt_data(encrypted_data: str):
    enc = get_encryption()
    return {"decrypted": enc.decrypt(encrypted_data)}

@router.post("/auth/register")
async def register_user(username: str, password: str, role: str = "user"):
    auth = get_auth()
    user_id = auth.create_user(username, password, role)
    return {"user_id": user_id, "status": "created"}

@router.post("/auth/login")
async def login(username: str, password: str):
    auth = get_auth()
    token = auth.authenticate(username, password)
    return {"token": token, "status": "success" if token else "failed"}

@router.get("/metrics")
async def get_metrics():
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return monitor.get_metrics()

@router.get("/alerts")
async def get_alerts():
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return {"alerts": monitor.get_alerts()}


# ── Browser Automation ──────────────────────────────────────────

@router.post("/browser/task")
async def browser_task(url: str, actions: list, user_id: str = "default"):
    from aeryn_core.platform.browser_vector import get_browser
    browser = get_browser()
    return browser.run_task(url, actions, user_id)

# ── Vector DB ──────────────────────────────────────────────────

@router.post("/vectordb/collections")
async def create_collection(name: str, dimension: int = 384, description: str = ""):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"collection": vdb.create_collection(name, dimension, description)}

@router.post("/vectordb/{collection}/add")
async def add_vectors(collection: str, texts: list, embeddings: list = None, metadatas: list = None):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    ids = vdb.add(collection, texts, embeddings, metadatas)
    return {"ids": ids}

@router.post("/vectordb/{collection}/search")
async def search_vectors(collection: str, query_embedding: list, limit: int = 5):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"results": vdb.search(collection, query_embedding, limit)}

@router.delete("/vectordb/{collection}")
async def delete_collection(collection: str):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    vdb.delete_collection(collection)
    return {"status": "deleted"}


# ── Monitoring Endpoints ──────────────────────

@router.get("/api/monitoring/sessions")
async def monitoring_sessions():
    """Get all chat sessions."""
    try:
        from pathlib import Path
        import sqlite3
        db_path = Path("Personalisasi/Database/conversations.db")
        if not db_path.exists():
            return {"sessions": []}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT session_id, COUNT(*) as messages, MAX(created_at) as last_active "
            "FROM conversations GROUP BY session_id ORDER BY last_active DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return {"sessions": [dict(r) for r in rows]}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@router.get("/api/monitoring/history")
async def monitoring_history(session_id: str, limit: int = 50):
    """Get conversation history for a session."""
    try:
        from pathlib import Path
        import sqlite3
        db_path = Path("Personalisasi/Database/conversations.db")
        if not db_path.exists():
            return {"session_id": session_id, "history": []}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content, reasoning, created_at FROM conversations "
            "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        conn.close()
        return {"session_id": session_id, "history": [dict(r) for r in rows]}
    except Exception as e:
        return {"session_id": session_id, "history": [], "error": str(e)}

@router.get("/api/adaptive/health")
async def adaptive_health():
    """Get adaptive system health report."""
    try:
        system = get_adaptive_system()
        return system.get_health_report()
    except Exception as e:
        return {"error": str(e), "status": "unknown"}


@router.get("/api/adaptive/errors")
async def adaptive_errors(hours: int = 24):
    """Get adaptive error summary."""
    try:
        system = get_adaptive_system()
        return system.get_error_summary(hours)
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/adaptive/adaptations")
async def adaptive_adaptations(hours: int = 24):
    """Get adaptive adaptation summary."""
    try:
        system = get_adaptive_system()
        return system.get_adaptation_summary(hours)
    except Exception as e:
        return {"error": str(e)}


@router.post("/api/adaptive/run-cycle")
async def adaptive_run_cycle():
    """Manually run a self-improvement cycle."""
    try:
        system = get_adaptive_system()
        return system.run_self_improvement_cycle()
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/monitoring/stats")
async def monitoring_stats():
    """Get monitoring statistics."""
    try:
        router = get_mode_router()
        llm = router.llm
        return {
            "total_requests": llm._request_count,
            "total_errors": llm._error_count,
            "active_sessions": len(router.sessions),
            "mode": router.mode,
        }
    except Exception as e:
        return {"error": str(e)}


# Dashboard web routes
from apps.web.server import router as dashboard_router

# SPA routes — serve dashboard HTML for client-side routing routes
@router.get("/", response_class=HTMLResponse)
async def spa_root():
    """Serve dashboard HTML for client-side routing pages."""
    from apps.web.server import _serve_dashboard
    return _serve_dashboard()

# Redirect all old SPA routes to single dashboard
for _route in ["/projects", "/workspaces", "/chat", "/audit", "/settings", "/notifications"]:
    def make_redirect():
        async def redirect():
            return RedirectResponse(url="/")
        return redirect
    _handler = make_redirect()
    _handler.__name__ = f"redirect_{_route.strip('/')}"
    # app.add_api_route(_route, endpoint=_handler)

@router.get("/app/{spa:path}", response_class=HTMLResponse)
async def spa_fallback(spa: str):
    """Serve dashboard HTML for client-side routing routes."""
    SPA_ROUTES = {"/", "/projects", "/workspaces", "/chat", "/plugins", "/audit", "/settings", "/notifications"}
    from apps.web.server import _serve_dashboard
    if "/" + spa in SPA_ROUTES:
        return _serve_dashboard()
    return JSONResponse({"error": "Not found"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
