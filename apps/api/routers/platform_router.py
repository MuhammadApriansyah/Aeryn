"""Platform Router — Browser, Cloud, GitHub, Discord, MCP, Multi-Agent, Skills."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/platform", tags=["platform"])


# ========================================
# Browser Automation
# ========================================

class BrowserRequest(BaseModel):
    url: str
    task: str = "scrape"


@router.post("/browser/scrape")
async def browser_scrape(req: BrowserRequest):
    """Quick scrape a URL."""
    from aeryn_core.platform.browser_automation import quick_scrape
    
    result = quick_scrape(req.url)
    return {"result": result}


@router.post("/browser/screenshot")
async def browser_screenshot(req: BrowserRequest):
    """Quick screenshot a URL."""
    from aeryn_core.platform.browser_automation import quick_screenshot
    
    result = quick_screenshot(req.url)
    return {"result": result}


@router.post("/browser/run-task")
async def browser_run_task(req: BrowserRequest):
    """Run a browser task."""
    from aeryn_core.platform.browser_automation import BrowserSession
    
    session = BrowserSession()
    session.start()
    result = session.navigate(req.url)
    session.close()
    
    return {"result": result}


# ========================================
# Cloud Sync
# ========================================

@router.post("/cloud/scan")
async def cloud_scan():
    """Scan files for cloud sync."""
    from aeryn_core.platform.cloud_sync import get_cloud_sync
    
    sync = get_cloud_sync()
    result = sync.scan_files()
    return {"result": result}


@router.post("/cloud/sync")
async def cloud_sync_files():
    """Sync files to cloud."""
    from aeryn_core.platform.cloud_sync import get_cloud_sync
    
    sync = get_cloud_sync()
    result = sync.sync_files()
    return {"result": result}


# ========================================
# GitHub Integration
# ========================================

class GitHubRequest(BaseModel):
    repo: str
    title: str
    body: str = ""


@router.post("/github/create-issue")
async def github_create_issue(req: GitHubRequest):
    """Create a GitHub issue."""
    from aeryn_core.platform.github_integration import get_github
    
    gh = get_github()
    result = gh.create_issue(req.repo, req.title, req.body)
    return {"result": result}


@router.post("/github/link-issue")
async def github_link_issue(req: GitHubRequest, pr_id: str = ""):
    """Link issue to PR."""
    from aeryn_core.platform.github_integration import get_github
    
    gh = get_github()
    result = gh.link_issue_to_pr(req.repo, req.title, pr_id)
    return {"result": result}


# ========================================
# Discord Bot
# ========================================

@router.get("/discord/commands")
async def discord_commands():
    """Get Discord bot commands."""
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    
    handler = DiscordBotHandler()
    commands = handler.get_commands()
    return {"commands": commands}


@router.post("/discord/register-command")
async def discord_register_command(name: str, description: str):
    """Register a Discord command."""
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    
    handler = DiscordBotHandler()
    result = handler.register_command(name, description)
    return {"result": result}


# ========================================
# Email Agent
# ========================================

class EmailRequest(BaseModel):
    email_text: str
    context: str = ""


@router.post("/email/triage")
async def email_triage(req: EmailRequest):
    """Triage an email."""
    from aeryn_core.platform.email_agent import get_email_agent
    
    agent = get_email_agent()
    result = agent.triage_email(req.email_text)
    return {"triage": result}


@router.post("/email/generate-reply")
async def email_generate_reply(req: EmailRequest):
    """Generate email reply."""
    from aeryn_core.platform.email_agent import get_email_agent
    
    agent = get_email_agent()
    result = agent.generate_reply(req.email_text, req.context)
    return {"reply": result}


# ========================================
# Calendar Integration
# ========================================

class CalendarEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str = ""
    description: str = ""


@router.post("/calendar/create-event")
async def calendar_create_event(req: CalendarEventRequest):
    """Create a calendar event."""
    from aeryn_core.platform.calendar_integration import get_calendar
    
    cal = get_calendar()
    result = cal.create_event(req.title, req.start_time, req.end_time, req.description)
    return {"result": result}


@router.get("/calendar/events")
async def calendar_events(start: str = "", end: str = ""):
    """Get calendar events."""
    from aeryn_core.platform.calendar_integration import get_calendar
    
    cal = get_calendar()
    events = cal.get_events(start, end)
    return {"events": events, "count": len(events)}


# ========================================
# MCP Production Server
# ========================================

@router.post("/mcp/create-key")
async def mcp_create_key(name: str):
    """Create MCP API key."""
    from aeryn_core.platform.mcp_production import get_mcp_production_server
    
    server = get_mcp_production_server()
    result = server.create_key(name)
    return {"key": result}


@router.get("/mcp/validate-key")
async def mcp_validate_key(key: str):
    """Validate MCP API key."""
    from aeryn_core.platform.mcp_production import get_mcp_production_server
    
    server = get_mcp_production_server()
    result = server.validate_key(key)
    return {"valid": result}


# ========================================
# Multi-Agent Orchestration
# ========================================

@router.post("/multi-agent/register")
async def multi_agent_register(agent_id: str, role: str):
    """Register an agent."""
    from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator
    
    orchestrator = get_multi_agent_orchestrator()
    result = orchestrator.register_agent_workflow_anchor(agent_id, role)
    return {"result": result}


@router.get("/multi-agent/agents")
async def multi_agent_list():
    """List registered agents."""
    from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator
    
    orchestrator = get_multi_agent_orchestrator()
    agents = orchestrator.get_agents()
    return {"agents": agents}


# ========================================
# Multi-Agent Rooms
# ========================================

class RoomRequest(BaseModel):
    room_id: str
    name: str = ""
    participants: List[str] = []


@router.post("/rooms/create")
async def rooms_create(req: RoomRequest):
    """Create a multi-agent room."""
    from aeryn_core.platform.multi_agent_rooms import get_room_manager
    
    manager = get_room_manager()
    result = manager.create_room(req.room_id, req.name, req.participants)
    return {"room": result}


@router.get("/rooms/{room_id}")
async def rooms_get(room_id: str):
    """Get room info."""
    from aeryn_core.platform.multi_agent_rooms import get_room_manager
    
    manager = get_room_manager()
    room = manager.get_room(room_id)
    return {"room": room}


# ========================================
# Multi-Tenant
# ========================================

class TenantRequest(BaseModel):
    tenant_id: str
    name: str = ""


@router.post("/tenants/create")
async def tenants_create(req: TenantRequest):
    """Create a tenant."""
    from aeryn_core.platform.multi_tenant import get_multi_tenant
    
    mt = get_multi_tenant()
    result = mt.create_tenant(req.tenant_id, req.name)
    return {"result": result}


@router.post("/tenants/add-user")
async def tenants_add_user(tenant_id: str, user_id: str):
    """Add user to tenant."""
    from aeryn_core.platform.multi_tenant import get_multi_tenant
    
    mt = get_multi_tenant()
    result = mt.add_user(tenant_id, user_id)
    return {"result": result}


# ========================================
# Skill Crystallization
# ========================================

@router.post("/skills/record-action")
async def skills_record_action(action: str, context: str = ""):
    """Record an action for skill crystallization."""
    from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
    
    crystallizer = get_skill_crystallizer()
    result = crystallizer.record_action(action, context)
    return {"result": result}


@router.get("/skills/frequent-patterns")
async def skills_frequent_patterns(limit: int = 10):
    """Get frequent patterns."""
    from aeryn_core.platform.skill_crystallization import PatternDetector
    
    detector = PatternDetector()
    patterns = detector.get_frequent_patterns(user_id="", min_frequency=limit)
    
    return {"patterns": patterns}


@router.post("/skills/crystallize")
async def skills_crystallize():
    """Crystallize skills from patterns."""
    from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
    
    crystallizer = get_skill_crystallizer()
    result = crystallizer.crystallize()
    return {"result": result}


# ========================================
# Webhook System
# ========================================

class WebhookRequest(BaseModel):
    url: str
    event: str
    secret: str = ""


@router.post("/webhooks/register")
async def webhooks_register(req: WebhookRequest):
    """Register a webhook."""
    from aeryn_core.platform.webhook_system import get_webhook_system
    
    ws = get_webhook_system()
    result = ws.register(req.url, req.event, req.secret)
    return {"result": result}


@router.post("/webhooks/trigger")
async def webhooks_trigger(event: str, data: Dict[str, Any] = None):
    """Trigger webhooks for an event."""
    from aeryn_core.platform.webhook_system import get_webhook_system
    
    ws = get_webhook_system()
    result = ws.trigger(event, data or {})
    return {"result": result}


# ========================================
# Sub-Agent Runner
# ========================================

class SubAgentRequest(BaseModel):
    sop: str
    args: List[str] = []


@router.post("/sub-agent/spawn")
async def sub_agent_spawn(req: SubAgentRequest):
    """Spawn sub-agents."""
    from aeryn_core.platform.sub_agent_runner import spawn_subagents
    
    result = spawn_subagents(req.sop, req.args)
    return {"result": result}


# ========================================
# Tool Bridge
# ========================================

@router.get("/tools/schemas")
async def tools_schemas():
    """Get tool schemas."""
    from aeryn_core.platform.tool_bridge import ToolGraduationRegistry
    
    registry = ToolGraduationRegistry()
    schemas = registry.schemas()
    return {"schemas": schemas}


@router.post("/tools/register")
async def tools_register(name: str, schema: Dict[str, Any]):
    """Register a tool."""
    from aeryn_core.platform.tool_bridge import ToolGraduationRegistry
    
    registry = ToolGraduationRegistry()
    result = registry.register(name, schema)
    return {"result": result}


# ========================================
# Tool Governance
# ========================================

class GovernanceRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}


@router.post("/tools/governance/evaluate")
async def tools_governance_evaluate(req: GovernanceRequest):
    """Evaluate tool governance."""
    from aeryn_core.platform.tool_governance import ToolGovernanceGate
    
    gate = ToolGovernanceGate()
    result = gate.evaluate(req.tool_name, req.args)
    return {"result": result}


# ========================================
# Health
# ========================================

@router.get("/health")
async def platform_health():
    """Platform module health check."""
    return {"status": "healthy", "module": "platform"}
