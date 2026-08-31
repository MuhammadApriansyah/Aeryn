"""V61.1 — Chat router for Aeryn API (with D2+D3 integration)."""
from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import os, sys, json, time, uuid, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.utils.llm_client import get_mode_router, AerynLLMClient
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.error_recovery import get_error_recovery
from aeryn_core.utils.logger import info, warn, error, log_exception

router = APIRouter()


def _route_to_division(goal: str):
    """Route goal to one of 5 Aeryn divisions based on intent."""
    goal_lower = goal.lower()
    if any(w in goal_lower for w in ["design", "creative", "style", "content", "write", "story", "art", "ui", "ux", "brand"]):
        return {"name": "creative", "description": "Creative & Design Division"}
    if any(w in goal_lower for w in ["analyze", "psychology", "emotion", "behavior", "sentiment", "feel", "mood", "personality"]):
        return {"name": "psych", "description": "Psychology & Analysis Division"}
    if any(w in goal_lower for w in ["reason", "logic", "math", "research", "code", "algorithm", "solve", "calculate", "debug", "explain"]):
        return {"name": "reasoning", "description": "Reasoning & Research Division"}
    if any(w in goal_lower for w in ["compliance", "security", "governance", "policy", "audit", "risk", "legal", "regulate"]):
        return {"name": "gov", "description": "Governance & Compliance Division"}
    if any(w in goal_lower for w in ["deploy", "infrastructure", "devops", "server", "docker", "kubernetes", "ci/cd", "monitor", "scale"]):
        return {"name": "infra", "description": "Infrastructure & DevOps Division"}
    return None


def _extract_tool_args(goal: str, tool_name: str):
    """Extract tool arguments from natural language goal."""
    args = {}
    goal_lower = goal.lower()
    if tool_name == "web_search":
        args["query"] = goal
    elif tool_name == "fs_read":
        import re
        match = re.search(r'(?:read|file|open)\s+(\S+)', goal_lower)
        if match:
            args["path"] = match.group(1)
    elif tool_name == "fs_list":
        args["path"] = "."
    elif tool_name == "terminal":
        args["command"] = goal
    elif tool_name == "memory_search":
        args["query"] = goal
        args["limit"] = 5
    return args


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



@router.post("/compile")
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

@router.post("/digest")
async def digest(req: DigestRequest):
    eng = get_safety_engine()
    clean_response = sanitize_output(req.response)
    vault = AerynVault()
    if len(req.user_prompt) > 10 and len(clean_response) > 10:
        try:
            vault.write(VaultEntry(layer=LAYER_WIKI, title=f"Conversation {req.session_id[:8]}", body=f"User: {req.user_prompt[:200]}\n\nResponse: {clean_response[:500]}", tags=["conversation", "auto"]))
        except Exception: pass
    return {"ok": True, "status": "digested", "accounting_ledger_audit": {"audit_payload": {"session_id": req.session_id, "timestamp": time.time()}}, "cog_mem_lifecycle_telemetry": {"focus_segment_retained": len(req.user_prompt) > 10}}

@router.post("/run")
async def run(req: RunRequest):
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    if not safety.safe: return {"status": "blocked", "safety": safety.to_dict()}
    
    start_time = time.time()
    research = needs_research(req.goal)
    adapter = get_active_adapter(req.goal)
    persona = load_persona()
    
    # D2: Dynamic Tool Execution — detect intent & execute tool if matched
    from aeryn_core.platform.plugin_registry import get_registry
    from aeryn_core.observability.tracer import get_tracer
    from aeryn_core.self_improvement.engine import get_self_improvement
    
    tracer = get_tracer()
    registry = get_registry()
    si = get_self_improvement()
    trace = tracer.start_trace(req.session_id)
    
    # Discover tools matching the goal
    matched_tools = registry.discover_tools(req.goal, limit=3)
    tool_result = None
    division_used = None
    
    # D3: Route to 5 divisions based on intent
    division = _route_to_division(req.goal)
    if division:
        division_used = division["name"]
        persona = f"{persona}\n\n[Division: {division['name']} — {division['description']}]"
    
    # Execute top tool if confidence high enough
    tool_name_used = None
    if matched_tools and matched_tools[0].get("score", 0) >= 5:
        top_tool = matched_tools[0]
        tool_name_used = top_tool["name"]
        span = tracer.start_span(f"tool:{top_tool['name']}", "tool", {"goal": req.goal}, trace_id=trace.id)
        try:
            args = _extract_tool_args(req.goal, top_tool["name"])
            tool_result = registry.call_tool(top_tool["name"], **args)
            tracer.finish_span(span.id, output=str(tool_result)[:500])
            
            # Record learning: tool selection outcome
            si.record_outcome("tool_selection", top_tool["name"], tool_result.get("ok", False), 
                            duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            tracer.finish_span(span.id, error=str(e))
            tool_result = {"ok": False, "error": str(e)}
            si.record_outcome("tool_selection", top_tool["name"], False)
    
    # Record division routing outcome
    if division_used:
        si.record_learning("division_routing", req.goal[:100], division_used, "routed", 
                          metadata={"goal": req.goal[:200]})
    
    # Build prompt
    prompt = f"{persona}\n\nUser: {req.goal}"
    if adapter: prompt += f"\n{render_adapter_context(req.goal)}"
    if tool_result and tool_result.get("ok"):
        prompt += f"\n\n[Tool Result from {tool_name_used}]: {str(tool_result.get('output', ''))[:1000]}"
    if division_used:
        prompt += f"\n\n[Routed to: {division_used} division]"
    
    # Get mode router
    router = get_mode_router()
    
    if router.is_standalone():
        try:
            messages = [
                {"role": "system", "content": persona},
                {"role": "user", "content": req.goal},
            ]
            llm_span = tracer.start_span("llm:chat", "llm", {"model": "default"}, trace_id=trace.id)
            result = await router.llm.chat(messages)
            tracer.finish_span(llm_span.id, output=result.get("content", "")[:200])
            response = result["content"]
            tracer.finish_trace(trace.id)
            
            # Record successful LLM call
            si.record_outcome("llm_call", result.get("provider", "unknown"), True,
                            duration_ms=int((time.time() - start_time) * 1000))
            
            return {
                "status": "ok",
                "session_id": req.session_id,
                "safety": safety.to_dict(),
                "adapter": adapter.name if adapter else None,
                "needs_research": research,
                "response": sanitize_output(response),
                "provider": result.get("provider"),
                "model": result.get("model"),
                "tool_used": tool_name_used,
                "tool_result": tool_result,
                "division": division_used,
            }
        except Exception as e:
            tracer.finish_trace(trace.id)
            si.record_outcome("llm_call", "unknown", False)
            return {"status": "error", "error": str(e), "session_id": req.session_id}
    else:
        response = f"Processing: {req.goal[:200]}"
        if adapter: response += f"\n[Adapter: {adapter.name}]"
        if research: response += "\n[Research needed]"
        if tool_result: response += f"\n[Tool: {tool_name_used}]"
        if division_used: response += f"\n[Division: {division_used}]"
        tracer.finish_trace(trace.id)
        return {
            "status": "ok",
            "session_id": req.session_id,
            "safety": safety.to_dict(),
            "response": response,
            "tool_used": tool_name_used,
            "division": division_used,
        }

@router.post("/chat")
async def chat(req: RunRequest):
    """Full chat endpoint with session + LLM (standalone mode)."""
    router = get_mode_router()
    
    if router.is_plugin():
        return await run(req)
    
    # Get or create session
    session = router.get_or_create_session(req.session_id)
    
    # Safety check
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    if not safety.safe:
        return {"status": "blocked", "safety": safety.to_dict()}
    
    # D2: Dynamic Tool Execution in chat
    from aeryn_core.platform.plugin_registry import get_registry
    from aeryn_core.observability.tracer import get_tracer
    tracer = get_tracer()
    registry = get_registry()
    trace = tracer.start_trace(req.session_id)
    
    # Discover & execute tool
    matched_tools = registry.discover_tools(req.goal, limit=3)
    tool_result = None
    division_used = None
    
    division = _route_to_division(req.goal)
    if division:
        division_used = division["name"]
    
    if matched_tools and matched_tools[0].get("score", 0) >= 5:
        top_tool = matched_tools[0]
        span = tracer.start_span(f"tool:{top_tool['name']}", "tool", {"goal": req.goal}, trace_id=trace.id)
        try:
            args = _extract_tool_args(req.goal, top_tool["name"])
            tool_result = registry.call_tool(top_tool["name"], **args)
            tracer.finish_span(span.id, output=str(tool_result)[:500])
        except Exception as e:
            tracer.finish_span(span.id, error=str(e))
            tool_result = {"ok": False, "error": str(e)}
    
    # Add user message
    session.add_message("user", req.goal)
    
    # Get context window with persona + tool result + division context
    persona = load_persona()
    if division_used:
        persona = f"{persona}\n\n[Division: {division['name']}]"
    
    system_msg = {"role": "system", "content": persona}
    messages = [system_msg] + session.get_context_window()
    
    # Add tool result to context
    if tool_result and tool_result.get("ok"):
        messages.append({"role": "assistant", "content": f"[Tool {matched_tools[0]['name']} executed]: {str(tool_result.get('output', ''))[:500]}"})
    
    # Call LLM
    try:
        result = await router.llm.chat(messages)
        response = result["content"]
        reasoning = result.get("reasoning", [])
        
        # Store response
        session.add_message("assistant", response, json.dumps(reasoning))
        tracer.finish_trace(trace.id)
        
        return {
            "status": "ok",
            "session_id": req.session_id,
            "response": response,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "tool_used": matched_tools[0]["name"] if tool_result else None,
            "division": division_used,
        }
    except Exception as e:
        tracer.finish_trace(trace.id)
        return {"status": "error", "error": str(e)}

@router.get("/search")
async def search(q: str, limit: int = 10):
    hse = get_search_engine()
    results = hse.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}

@router.get("/dashboard")
async def dashboard():
    """Serve monitoring dashboard HTML."""
    return FileResponse("apps/api/dashboard.html")

@router.get("/chat")
async def web_chat():
    """Serve web chat interface."""
    return Response(content=WEB_CHAT_HTML, media_type="text/html")

WEB_CHAT_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aeryn Chat</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: system-ui; background:#09090b; color:#fafafa; height:100vh; display:flex; flex-direction:column; }
#header { padding:16px 24px; background:#18181b; border-bottom:1px solid #27272a; display:flex; align-items:center; gap:12px; }
#header h1 { font-size:18px; }
#status { width:8px; height:8px; border-radius:50%; background:#f87171; }
#status.online { background:#4ade80; }
#messages { flex:1; overflow-y:auto; padding:24px; display:flex; flex-direction:column; gap:16px; }
.message { max-width:70%; padding:12px 16px; border-radius:12px; line-height:1.5; }
.message.user { align-self:flex-end; background:#22d3ee; color:#09090b; }
.message.assistant { align-self:flex-start; background:#27272a; }
.message .role { font-size:11px; opacity:0.7; margin-bottom:4px; }
#input-area { padding:16px 24px; background:#18181b; border-top:1px solid #27272a; display:flex; gap:12px; }
#input { flex:1; padding:12px 16px; border:none; border-radius:8px; background:#27272a; color:#fafafa; font-size:14px; outline:none; }
#send { padding:12px 24px; border:none; border-radius:8px; background:#22d3ee; color:#09090b; font-weight:600; cursor:pointer; }
#send:hover { background:#06b6d4; }
</style>
</head>
<body>
<div id="header">
    <div id="status"></div>
    <h1>Aeryn Chat</h1>
</div>
<div id="messages"></div>
<div id="input-area">
    <input id="input" placeholder="Type a message..." autocomplete="off">
    <button id="send" onclick="send()">Send</button>
</div>
<script>
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const status = document.getElementById('status');
let sessionId = 'web_' + Date.now();

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = '<div class="role">' + role + '</div>' + content.replace(/\\n/g, '<br>');
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function send() {
    const text = input.value.trim();
    if (!text) return;
    addMessage('user', text);
    input.value = '';
    
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({goal: text, session_id: sessionId})
        });
        const data = await res.json();
        addMessage('assistant', data.response || JSON.stringify(data));
    } catch(e) {
        addMessage('assistant', 'Error: ' + e.message);
    }
}

input.addEventListener('keypress', (e) => { if(e.key === 'Enter') send(); });

// Check status
fetch('/health').then(r => r.json()).then(d => {
    if(d.status === 'healthy') status.className = 'online';
}).catch(() => {});
</script>
</body>
</html>"""
