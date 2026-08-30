"""V61.0 — Chat router for Aeryn API."""
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

@router.get("/health")
async def health():
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "61.0"}
    except ImportError:
        return {"status": "healthy", "version": "61.0"}

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
    
    research = needs_research(req.goal)
    adapter = get_active_adapter(req.goal)
    persona = load_persona()
    
    # Build prompt
    prompt = f"{persona}\n\nUser: {req.goal}"
    if adapter: prompt += f"\n{render_adapter_context(req.goal)}"
    
    # Get mode router
    router = get_mode_router()
    
    if router.is_standalone():
        # Standalone mode: call LLM directly
        try:
            messages = [
                {"role": "system", "content": persona},
                {"role": "user", "content": req.goal},
            ]
            result = await router.llm.chat(messages)
            response = result["content"]
            return {
                "status": "ok",
                "session_id": req.session_id,
                "safety": safety.to_dict(),
                "adapter": adapter.name if adapter else None,
                "needs_research": research,
                "response": sanitize_output(response),
                "provider": result.get("provider"),
                "model": result.get("model"),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": req.session_id,
            }
    else:
        # Plugin mode: return prompt for Hermes to process
        response = f"Processing: {req.goal[:200]}"
        if adapter: response += f"\n[Adapter: {adapter.name}]"
        if research: response += "\n[Research needed]"
        return {
            "status": "ok",
            "session_id": req.session_id,
            "safety": safety.to_dict(),
            "adapter": adapter.name if adapter else None,
            "needs_research": research,
            "response": sanitize_output(response),
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
    
    # Add user message
    session.add_message("user", req.goal)
    
    # Get context window
    messages = [
        {"role": "system", "content": load_persona()},
    ] + session.get_context_window()
    
    # Call LLM
    try:
        result = await router.llm.chat(messages)
        response = result["content"]
        reasoning = result.get("reasoning", [])

        # Store response
        session.add_message("assistant", response, json.dumps(reasoning))
        
        return {
            "status": "ok",
            "session_id": req.session_id,
            "response": response,
            "provider": result.get("provider"),
            "model": result.get("model"),
        }
    except Exception as e:
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
    return Response(
        content=WEB_CHAT_HTML,
        media_type="text/html",
    )

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
