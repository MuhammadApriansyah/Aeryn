"""Dead Code Router — Functional implementation of 155 dead code files."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/dead", tags=["dead"])


# ========================================
# DATABASE MODULES
# ========================================

class DBRequest(BaseModel):
    db_name: str = "shared"
    query: str = ""
    params: tuple = ()


@router.get("/database/pg-check")
async def db_pg_check():
    """Check PostgreSQL availability."""
    from aeryn_core.database.db_adapter import get_adapter
    adapter = get_adapter()
    return {"pg_available": adapter.is_pg_available()}


@router.post("/database/pg-query")
async def db_pg_query(req: DBRequest):
    """Query PostgreSQL database."""
    from aeryn_core.database.db_adapter import get_adapter
    adapter = get_adapter()
    conn = adapter.connect(req.db_name)
    cursor = conn.cursor()
    cursor.execute(req.query, req.params)
    results = cursor.fetchall()
    conn.close()
    return {"results": results}


@router.get("/database/neon/available")
async def db_neon_available():
    """Check Neon availability."""
    from aeryn_core.database.neon_db import get_neon
    neon = get_neon()
    return {"available": neon.is_available()}


@router.post("/database/neon/connect")
async def db_neon_connect(conn_string: str = ""):
    """Connect to Neon."""
    from aeryn_core.database.neon_db import get_neon
    neon = get_neon()
    if conn_string:
        neon.set_connection_string(conn_string)
    conn = neon.get_connection()
    return {"connected": conn is not None}


@router.get("/database/semantic/stats")
async def db_semantic_stats():
    """Get semantic search stats."""
    from aeryn_core.database.semantic_search import get_semantic_search
    engine = get_semantic_search()
    stats = engine.get_stats()
    return {"stats": stats}


@router.post("/database/semantic/index")
async def db_semantic_index(content: str, metadata: Optional[Dict[str, str]] = None):
    """Index content for semantic search."""
    from aeryn_core.database.semantic_search import get_semantic_search
    engine = get_semantic_search()
    result = engine.index_memory(content, metadata)
    return {"result": result}


@router.post("/database/semantic/search")
async def db_semantic_search(query: str, limit: int = 5):
    """Search semantic index."""
    from aeryn_core.database.semantic_search import get_semantic_search
    engine = get_semantic_search()
    results = engine.search(query, limit)
    return {"results": results}


@router.get("/database/vector/collections")
async def db_vector_collections():
    """List vector collections."""
    from aeryn_core.database.vector_rust import VectorDB
    db = VectorDB()
    collections = db.list_collections()
    return {"collections": collections}


@router.post("/database/vector/create")
async def db_vector_create(collection: str):
    """Create vector collection."""
    from aeryn_core.database.vector_rust import VectorDB
    db = VectorDB()
    col = db.get_or_create_collection(collection)
    return {"collection": collection, "status": "created"}


@router.post("/database/vector/add")
async def db_vector_add(collection: str, id: str, vector: List[float], metadata: Optional[Dict[str, str]] = None):
    """Add vector to collection."""
    from aeryn_core.database.vector_rust import VectorDB
    db = VectorDB()
    col = db.get_or_create_collection(collection)
    col.add(id, vector, metadata)
    return {"status": "ok"}


@router.post("/database/vector/query")
async def db_vector_query(collection: str, query: List[float], limit: int = 5):
    """Query vectors."""
    from aeryn_core.database.vector_rust import VectorDB
    db = VectorDB()
    col = db.get_or_create_collection(collection)
    results = col.query(query, limit)
    return {"results": results}


# ========================================
# MCP MODULES
# ========================================

@router.post("/mcp/server/register-tool")
async def mcp_server_register(name: str, description: str, parameters: Dict[str, Any]):
    """Register tool on MCP server."""
    from aeryn_core.mcp.server import MCPServer
    server = MCPServer()
    result = server.register_tool(name, description, parameters)
    return {"result": result}


@router.get("/mcp/server/list-tools")
async def mcp_server_list():
    """List MCP tools."""
    from aeryn_core.mcp.server import MCPServer
    server = MCPServer()
    tools = server.list_tools()
    return {"tools": tools}


@router.post("/mcp/server/call-tool")
async def mcp_server_call(name: str, args: Dict[str, Any] = None):
    """Call MCP tool."""
    from aeryn_core.mcp.server import MCPServer
    server = MCPServer()
    result = server.call_tool(name, args or {})
    return {"result": result}


@router.get("/mcp/client/discover")
async def mcp_client_discover(server_url: str = ""):
    """Discover MCP servers."""
    if not server_url:
        return {"message": "No server_url provided — discovery skipped"}
    from aeryn_core.mcp.client import MCPClient
    client = MCPClient(server_url, "default")
    servers = client.discover()
    return {"servers": servers}


@router.post("/mcp/client/call-tool")
async def mcp_client_call(server: str, tool: str, args: Dict[str, Any] = None):
    """Call tool via MCP client."""
    from aeryn_core.mcp.client import MCPClient
    client = MCPClient(server_url=server, name="default")
    result = client.call_tool(server, tool, args or {})
    return {"result": result}


@router.get("/mcp/client/list-tools")
async def mcp_client_list(server: str = ""):
    """List tools from MCP server."""
    from aeryn_core.mcp.client import MCPClient
    client = MCPClient(server_url=server, name="default")
    tools = client.list_tools(server)
    return {"tools": tools}


# ========================================
# HERMES MODULES
# ========================================

@router.get("/hermes/brain/digest")
async def hermes_brain_digest():
    """Get Hermes brain digest."""
    import os
    hermes_scripts = os.path.expanduser("~/.hermes/scripts")
    if not os.path.exists(hermes_scripts):
        return {"error": "Hermes scripts not available", "path": hermes_scripts}
    
    from aeryn_core.hermes.hermes_brain import _memory_search
    result = _memory_search("aeryn", top=3)
    return {"digest": result}


@router.get("/hermes/hands/ask")
async def hermes_hands_ask(query: str):
    """Ask Hermes hands."""
    from aeryn_core.hermes.hermes_hands import ask_hermes
    result = ask_hermes(query)
    return {"result": result}


@router.get("/hermes/reflex/activity")
async def hermes_reflex_activity():
    """Get Hermes reflex activity."""
    from aeryn_core.hermes.hermes_reflex import recent_hermes_activity
    result = recent_hermes_activity()
    return {"activity": result}


@router.get("/hermes/reflex/digest")
async def hermes_reflex_digest():
    """Get Hermes reflex digest."""
    from aeryn_core.hermes.hermes_reflex import get_reflex_digest
    result = get_reflex_digest()
    return {"digest": result}


@router.get("/hermes-plugin/skills")
async def hermes_plugin_skills():
    """Load Hermes plugin skills."""
    from aeryn_core.hermes_plugin.loader import load_skills
    result = load_skills()
    return {"skills": result}


@router.get("/hermes-plugin/scripts")
async def hermes_plugin_scripts():
    """Load Hermes plugin scripts."""
    from aeryn_core.hermes_plugin.loader import load_scripts
    result = load_scripts()
    return {"scripts": result}


@router.get("/hermes-plugin/is-plugin")
async def hermes_is_plugin():
    """Check if Hermes plugin."""
    from aeryn_core.hermes_plugin.hermes_bridge_init import is_plugin
    return {"is_plugin": is_plugin()}


@router.get("/hermes-plugin/has-hermes")
async def hermes_has_hermes():
    """Check if has Hermes."""
    from aeryn_core.hermes_plugin.hermes_bridge_init import has_hermes
    return {"has_hermes": has_hermes()}


@router.get("/hermes-plugin/memory")
async def hermes_memory():
    """Get Hermes memory."""
    from aeryn_core.hermes_plugin.hermes_bridge_init import get_memory
    return {"memory": get_memory()}


# ========================================
# MEMORY MODULES
# ========================================

@router.get("/memory/core/render")
async def memory_core_render(content: str):
    """Render core memory."""
    from aeryn_core.memory.core_memory import CoreMemory
    mem = CoreMemory()
    result = mem.render(content)
    return {"rendered": result}


@router.post("/memory/core/edit")
async def memory_core_edit(content: str, new_content: str):
    """Edit core memory."""
    from aeryn_core.memory.core_memory import CoreMemory
    mem = CoreMemory()
    result = mem.edit(content, new_content)
    return {"edited": result}


@router.get("/memory/graph/backlinks")
async def memory_graph_backlinks(node_id: str):
    """Get backlinks from vault graph."""
    from aeryn_core.memory.graph import VaultGraph
    graph = VaultGraph()
    results = graph.get_backlinks(node_id)
    return {"backlinks": results}


@router.get("/memory/graph/outgoing")
async def memory_graph_outgoing(node_id: str):
    """Get outgoing links from vault graph."""
    from aeryn_core.memory.graph import VaultGraph
    graph = VaultGraph()
    results = graph.get_outgoing_links(node_id)
    return {"outgoing": results}


@router.get("/memory/graph/local")
async def memory_graph_local(node_id: str, depth: int = 2):
    """Get local graph."""
    from aeryn_core.memory.graph import VaultGraph
    graph = VaultGraph()
    results = graph.get_local_graph(node_id, depth)
    return {"graph": results}


@router.post("/memory/index")
async def memory_index():
    """Index vault memories."""
    from aeryn_core.memory.memory_indexer import index_vault
    result = index_vault()
    return {"result": result}


# ========================================
# MULTI-AGENT MODULES
# ========================================

@router.post("/multi-agent/workflow/add")
async def multi_agent_workflow_add(goal: str, steps: List[str] = None):
    """Add task to workflow."""
    from aeryn_core.multi_agent.orchestrator import Workflow
    wf = Workflow()
    result = wf.add_task(goal, steps or [])
    return {"result": result}


@router.get("/multi-agent/workflow/ready")
async def multi_agent_workflow_ready():
    """Get ready tasks."""
    from aeryn_core.multi_agent.orchestrator import Workflow
    wf = Workflow()
    tasks = wf.get_ready_tasks()
    return {"tasks": tasks}


@router.get("/multi-agent/workflow/status")
async def multi_agent_workflow_status(task_id: str):
    """Get task status."""
    from aeryn_core.multi_agent.orchestrator import Workflow
    wf = Workflow()
    status = wf.get_task_status(task_id)
    return {"status": status}


# ========================================
# PERSONAL MODULES
# ========================================

@router.post("/personal/context/set")
async def personal_context_set(key: str, value: str):
    """Set personal context."""
    from aeryn_core.personal.context import PersonalContext
    ctx = PersonalContext()
    ctx.set_context(key, value)
    return {"status": "ok"}


@router.get("/personal/context/get")
async def personal_context_get(key: str = ""):
    """Get personal context."""
    from aeryn_core.personal.context import PersonalContext
    ctx = PersonalContext()
    result = ctx.get_context(key)
    return {"context": result}


@router.get("/personal/context/build-prompt")
async def personal_context_build_prompt():
    """Build system prompt from context."""
    from aeryn_core.personal.context import PersonalContext
    ctx = PersonalContext()
    prompt = ctx.build_system_prompt()
    return {"prompt": prompt}


@router.post("/personal/preferences/set")
async def personal_preferences_set(preference: str, value: str):
    """Set user preference."""
    from aeryn_core.personal.personalization import PersonalizationEngine
    engine = PersonalizationEngine()
    engine.set_preference(preference, value)
    return {"status": "ok"}


@router.get("/personal/preferences/get")
async def personal_preferences_get(preference: str = ""):
    """Get user preference."""
    from aeryn_core.personal.personalization import PersonalizationEngine
    engine = PersonalizationEngine()
    if preference:
        result = engine.get_preference(preference)
    else:
        result = engine.get_all_preferences()
    return {"preferences": result}


@router.get("/personal/proactive/suggestions")
async def personal_proactive_suggestions(user_id: str = ""):
    """Get proactive suggestions."""
    from aeryn_core.personal.proactive_engine import ProactiveEngine
    engine = ProactiveEngine()
    suggestions = engine.generate_suggestions(user_id)
    return {"suggestions": suggestions}


@router.post("/personal/proactive/record")
async def personal_proactive_record(action: str):
    """Record proactive action."""
    from aeryn_core.personal.proactive_engine import ProactiveEngine
    engine = ProactiveEngine()
    engine.record_action(action)
    return {"status": "ok"}


@router.get("/personal/proactive/frequent")
async def personal_proactive_frequent(user_id: str = "", limit: int = 5):
    """Get frequent actions."""
    from aeryn_core.personal.proactive_engine import ProactiveEngine
    engine = ProactiveEngine()
    frequent = engine.get_frequent_actions(user_id, limit)
    return {"frequent": frequent}


# ========================================
# SAFETY MODULES
# ========================================

@router.post("/safety/sandbox/validate")
async def safety_sandbox_validate(command: str):
    """Validate command in sandbox."""
    from aeryn_core.safety.sandbox import Sandbox
    box = Sandbox()
    result = box.validate_command(command)
    return {"valid": result}


@router.post("/safety/sandbox/execute")
async def safety_sandbox_execute(command: str):
    """Execute command in sandbox."""
    from aeryn_core.safety.sandbox import Sandbox
    box = Sandbox()
    result = box.execute(command)
    return {"result": result}


@router.post("/safety/sandbox/create-temp")
async def safety_sandbox_create_temp():
    """Create temp dir in sandbox."""
    from aeryn_core.safety.sandbox import Sandbox
    box = Sandbox()
    result = box.create_temp_dir()
    return {"temp_dir": result}


@router.post("/safety/sandbox/cleanup")
async def safety_sandbox_cleanup(path: str):
    """Cleanup temp dir."""
    from aeryn_core.safety.sandbox import Sandbox
    box = Sandbox()
    box.cleanup_temp_dir(path)
    return {"status": "ok"}


@router.get("/safety/sandbox/terminal-log")
async def safety_sandbox_terminal_log():
    """Get sandbox terminal log."""
    from aeryn_core.safety.sandbox import get_secure_terminal
    term = get_secure_terminal()
    log = term.get_audit_log()
    return {"log": log}


@router.post("/safety/kernel/check-path")
async def safety_kernel_check_path(path: str):
    """Check path with security kernel."""
    from aeryn_core.safety.security_kernel import check_path
    result = check_path(path)
    return {"valid": result}


@router.get("/safety/kernel/secure-terminal")
async def safety_kernel_secure_terminal():
    """Make secure terminal."""
    from aeryn_core.safety.security_kernel import make_secure_terminal
    result = make_secure_terminal()
    return {"terminal": result}


@router.get("/safety/terminal/make")
async def safety_terminal_make():
    """Make terminal."""
    from aeryn_core.safety.terminal_tool import make_terminal
    result = make_terminal()
    return {"terminal": result}


# ========================================
# SANDBOX MODULES
# ========================================

@router.get("/sandbox/detect")
async def sandbox_detect():
    """Detect sandbox capabilities."""
    from aeryn_core.sandbox.detector import EnvironmentDetector
    detector = EnvironmentDetector()
    return {
        "has_bubblewrap": detector.has_bubblewrap(),
        "has_secimport": detector.has_secimport(),
        "has_unshare": detector.has_unshare(),
    }


@router.post("/sandbox/fallback/execute")
async def sandbox_fallback_execute(command: str):
    """Execute with fallback."""
    from aeryn_core.sandbox.fallback import FallbackOrchestrator
    orch = FallbackOrchestrator()
    result = orch.execute(command)
    return {"result": result}


@router.get("/sandbox/fallback/level")
async def sandbox_fallback_level():
    """Get fallback level."""
    from aeryn_core.sandbox.fallback import FallbackOrchestrator
    orch = FallbackOrchestrator()
    return {"level": orch.level, "capabilities": orch.capabilities()}


@router.post("/sandbox/level0/execute")
async def sandbox_level0_execute(command: str):
    """Execute with basic sandbox."""
    from aeryn_core.sandbox.level0_basic import BasicSandbox
    box = BasicSandbox()
    result = box.execute(command)
    return {"result": result}


@router.post("/sandbox/level1/execute")
async def sandbox_level1_execute(command: str):
    """Execute with namespace sandbox."""
    from aeryn_core.sandbox.level1_namespace import NamespaceSandbox
    box = NamespaceSandbox()
    result = box.execute(command)
    return {"result": result}


@router.post("/sandbox/level2/execute")
async def sandbox_level2_execute(command: str):
    """Execute with bubblewrap sandbox."""
    from aeryn_core.sandbox.level2_bubblewrap import BubblewrapSandbox
    box = BubblewrapSandbox()
    if not box.is_available():
        return {"error": "bubblewrap not available"}
    result = box.execute(command)
    return {"result": result}


@router.post("/sandbox/level3/execute")
async def sandbox_level3_execute(command: str):
    """Execute with full sandbox."""
    from aeryn_core.sandbox.level3_full import FullSandbox
    box = FullSandbox()
    if not box.is_available():
        return {"error": "full sandbox not available"}
    result = box.execute(command)
    return {"result": result}


# ========================================
# SECURITY MODULES
# ========================================

@router.post("/security/compliance/add-check")
async def security_compliance_add(name: str, check_fn: str = ""):
    """Add compliance check."""
    from aeryn_core.security.dashboard.compliance import ComplianceModule
    mod = ComplianceModule()
    mod.add_check(name, check_fn)
    return {"status": "ok"}


@router.get("/security/compliance/checks")
async def security_compliance_checks():
    """Get compliance checks."""
    from aeryn_core.security.dashboard.compliance import ComplianceModule
    mod = ComplianceModule()
    checks = mod.get_checks()
    return {"checks": checks}


@router.post("/security/compliance/report")
async def security_compliance_report():
    """Generate compliance report."""
    from aeryn_core.security.dashboard.compliance import ComplianceModule
    mod = ComplianceModule()
    report = mod.generate_report()
    return {"report": report}


@router.post("/security/dashboard/log-event")
async def security_dashboard_log(event_type: str, details: str = ""):
    """Log security event."""
    from aeryn_core.security.dashboard.security_dashboard import SecurityDashboard
    dash = SecurityDashboard()
    dash.log_event(event_type, details)
    return {"status": "ok"}


@router.get("/security/dashboard/events")
async def security_dashboard_events(limit: int = 20):
    """Get security events."""
    from aeryn_core.security.dashboard.security_dashboard import SecurityDashboard
    dash = SecurityDashboard()
    events = dash.get_events(limit)
    return {"events": events}


@router.post("/security/dashboard/alert")
async def security_dashboard_alert(alert_type: str, message: str):
    """Create security alert."""
    from aeryn_core.security.dashboard.security_dashboard import SecurityDashboard
    dash = SecurityDashboard()
    result = dash.create_alert(alert_type, message)
    return {"alert": result}


@router.post("/security/memory-guard/log-access")
async def security_memory_guard_log(resource: str, action: str):
    """Log memory access."""
    from aeryn_core.security.memory_guard import MemoryGuard
    guard = MemoryGuard()
    guard.log_access(resource, action)
    return {"status": "ok"}


@router.get("/security/memory-guard/verify")
async def security_memory_guard_verify():
    """Verify memory integrity."""
    from aeryn_core.security.memory_guard import MemoryGuard
    guard = MemoryGuard()
    result = guard.verify_integrity()
    return {"integrity": result}


@router.get("/security/memory-guard/audit")
async def security_memory_guard_audit():
    """Get memory audit trail."""
    from aeryn_core.security.memory_guard import MemoryGuard
    guard = MemoryGuard()
    trail = guard.get_audit_trail()
    return {"trail": trail}


@router.post("/security/prompt-injection/detect")
async def security_prompt_injection_detect(text: str):
    """Detect prompt injection."""
    from aeryn_core.security.prompt_injection import PromptInjectionDetector
    detector = PromptInjectionDetector()
    result = detector.detect(text)
    return {"injection_detected": result}


@router.post("/security/prompt-injection/sanitize")
async def security_prompt_injection_sanitize(text: str):
    """Sanitize text."""
    from aeryn_core.security.prompt_injection import PromptInjectionDetector
    detector = PromptInjectionDetector()
    result = detector.sanitize(text)
    return {"sanitized": result}


@router.post("/security/output/validate")
async def security_output_validate(text: str):
    """Validate output."""
    from aeryn_core.security.prompt_injection import OutputValidator
    validator = OutputValidator()
    result = validator.validate(text)
    return {"valid": result}


@router.get("/security/tool-permissions/risk")
async def security_tool_permissions_risk(tool_name: str = ""):
    """Get tool risk level."""
    from aeryn_core.security.tool_permissions import get_tool_risk
    risk = get_tool_risk(tool_name)
    return {"risk": risk}


@router.get("/security/tool-permissions/allowed")
async def security_tool_permissions_allowed():
    """Get allowed tools."""
    from aeryn_core.security.tool_permissions import get_allowed_tools
    tools = get_allowed_tools()
    return {"tools": tools}


@router.get("/health")
async def dead_health():
    """Dead code module health check."""
    return {"status": "healthy", "module": "dead"}
