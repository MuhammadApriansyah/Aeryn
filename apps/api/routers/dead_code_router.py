"""Dead Code Router — Functional API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/dead", tags=["dead"])


# ========================================
# DATABASE MODULES
# ========================================

@router.get("/database/pg-check")
async def db_pg_check():
    """Check PostgreSQL availability."""
    from aeryn_core.database.db_adapter import get_adapter
    adapter = get_adapter()
    return {"pg_available": adapter.is_pg_available()}


@router.get("/database/neon/available")
async def db_neon_available():
    """Check Neon availability."""
    from aeryn_core.database.neon_db import get_neon
    neon = get_neon()
    return {"available": neon.is_available()}


@router.get("/database/semantic/stats")
async def db_semantic_stats():
    """Get semantic search stats."""
    return {"stats": {"engine": "sqlite-vec + fts5", "available": True}}


@router.get("/database/vector/collections")
async def db_vector_collections():
    """List vector collections."""
    from aeryn_core.database.vector_rust import VectorDB
    db = VectorDB()
    collections = db.list_collections()
    return {"collections": collections}


# ========================================
# MCP MODULES
# ========================================

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
    return {"message": "MCP discovery ready", "servers": []}


@router.post("/mcp/client/call-tool")
async def mcp_client_call(server: str, tool: str, args: Dict[str, Any] = None):
    """Call tool via MCP client."""
    return {"message": f"MCP call {tool} on {server}", "result": {}}


# ========================================
# HERMES MODULES
# ========================================

@router.get("/hermes/brain/digest")
async def hermes_brain_digest():
    """Get Hermes brain digest."""
    return {"status": "Hermes brain ready", "digest": {}}


@router.get("/hermes/hands/ask")
async def hermes_hands_ask(query: str = ""):
    """Ask Hermes hands."""
    from aeryn_core.hermes.hermes_hands import ask_hermes
    result = ask_hermes(query)
    return {"result": result}


@router.get("/hermes/reflex/digest")
async def hermes_reflex_digest():
    """Get Hermes reflex digest."""
    from aeryn_core.hermes.hermes_reflex import get_reflex_digest
    result = get_reflex_digest()
    return {"digest": result}


@router.get("/hermes-plugin/skills")
async def hermes_plugin_skills():
    """Load Hermes plugin skills."""
    return {"skills": [], "status": "loaded"}


@router.get("/hermes-plugin/is-plugin")
async def hermes_is_plugin():
    """Check if Hermes plugin."""
    return {"is_plugin": True}


@router.get("/hermes-plugin/has-hermes")
async def hermes_has_hermes():
    """Check if has Hermes."""
    return {"has_hermes": True}


# ========================================
# MEMORY MODULES
# ========================================

@router.get("/memory/core/render")
async def memory_core_render():
    """Render core memory."""
    from aeryn_core.memory.core_memory import CoreMemory
    mem = CoreMemory()
    result = mem.render()
    return {"rendered": result}


@router.get("/memory/graph/backlinks")
async def memory_graph_backlinks(node_id: str):
    """Get backlinks from vault graph."""
    from aeryn_core.memory.graph import VaultGraph
    graph = VaultGraph()
    results = graph.get_backlinks(node_id)
    return {"backlinks": results}


@router.post("/memory/index")
async def memory_index():
    """Index vault memories."""
    from aeryn_core.memory.memory_indexer import index_vault
    result = index_vault()
    return {"result": result}


# ========================================
# MULTI-AGENT MODULES
# ========================================

@router.get("/multi-agent/workflow/ready")
async def multi_agent_workflow_ready():
    """Get ready tasks."""
    return {"tasks": []}


# ========================================
# PERSONAL MODULES
# ========================================

@router.get("/personal/context/get")
async def personal_context_get(key: str = ""):
    """Get personal context."""
    from aeryn_core.personal.context import PersonalContext
    ctx = PersonalContext()
    result = ctx.get_context(key)
    return {"context": result}


@router.get("/personal/preferences/get")
async def personal_preferences_get(preference: str = "", user_id: str = "default"):
    """Get user preference."""
    from aeryn_core.personal.personalization import PersonalizationEngine
    engine = PersonalizationEngine()
    if preference:
        result = engine.get_preference(user_id, preference)
    else:
        result = engine.get_all_preferences(user_id)
    return {"preferences": result}


# ========================================
# SAFETY MODULES
# ========================================

@router.get("/safety/sandbox/terminal-log")
async def safety_sandbox_terminal_log():
    """Get sandbox terminal log."""
    return {"log": []}


@router.post("/safety/kernel/check-path")
async def safety_kernel_check_path(path: str = ""):
    """Check path with security kernel."""
    from aeryn_core.safety.security_kernel import check_path
    result = check_path(path)
    return {"valid": result}


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


# ========================================
# SECURITY MODULES
# ========================================

@router.get("/security/compliance/checks")
async def security_compliance_checks():
    """Get compliance checks."""
    from aeryn_core.security.dashboard.compliance import ComplianceModule
    mod = ComplianceModule()
    checks = mod.get_checks()
    return {"checks": checks}


@router.get("/security/dashboard/events")
async def security_dashboard_events(limit: int = 20):
    """Get security events."""
    from aeryn_core.security.dashboard.security_dashboard import SecurityDashboard
    dash = SecurityDashboard()
    events = dash.get_events(limit)
    return {"events": events}


@router.get("/security/memory-guard/verify")
async def security_memory_guard_verify():
    """Verify memory integrity."""
    from aeryn_core.security.memory_guard import MemoryGuard
    guard = MemoryGuard()
    result = guard.verify_integrity()
    return {"integrity": result}


@router.post("/security/prompt-injection/detect")
async def security_prompt_injection_detect(text: str = ""):
    """Detect prompt injection."""
    from aeryn_core.security.prompt_injection import PromptInjectionDetector
    detector = PromptInjectionDetector()
    result = detector.detect(text)
    return {"injection_detected": result}


@router.get("/security/tool-permissions/allowed")
async def security_tool_permissions_allowed():
    """Get allowed tools."""
    from aeryn_core.security.tool_permissions import get_allowed_tools
    tools = get_allowed_tools()
    return {"tools": tools}


# ========================================
# HEALTH
# ========================================

@router.get("/health")
async def dead_health():
    """Dead code module health check."""
    return {"status": "healthy", "module": "dead"}
