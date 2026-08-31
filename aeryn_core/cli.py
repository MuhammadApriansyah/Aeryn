#!/usr/bin/env python3
"""V61.1 — Aeryn CLI: Interactive terminal interface.

Usage:
    python -m aeryn_core.cli [command] [args]
    
Commands:
    start       Start Aeryn services
    stop        Stop Aeryn services  
    status      Show service status
    chat        Interactive chat mode
    run         Run a single goal
    search      Search memory/vault
    tools       List registered tools
    divisions   List 5 cognitive divisions
    workflows   Manage workflows
    traces      View observability traces
    adapt       Trigger self-improvement
    env         Show environment info
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import shutil

API_BASE = os.environ.get("AERYN_API", "http://127.0.0.1:3010")


def api_get(path):
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def api_post(path, data=None):
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(
            f"{API_BASE}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def cmd_start(args):
    """Start Aeryn services."""
    print("🚀 Starting Aeryn...")
    if shutil.which("pm2"):
        os.system("pm2 start ecosystem.config.cjs")
        print("  ✅ Started via PM2")
    else:
        print("  ⚠️ PM2 not found. Install with: npm install -g pm2")
    cmd_status([])


def cmd_stop(args):
    """Stop Aeryn services."""
    print("🛑 Stopping Aeryn...")
    if shutil.which("pm2"):
        os.system("pm2 stop aeryn-api aeryn-dashboard")
    os.system("pkill -f 'routers/main.py' 2>/dev/null")
    print("  ✅ Stopped")


def cmd_status(args):
    """Show service status."""
    print("📊 Aeryn Status")
    health = api_get("/health")
    if "error" in health:
        print(f"  ❌ API unreachable: {health['error']}")
        return
    
    print(f"  Status: {health.get('status', '?')}")
    print(f"  Memory: {health.get('memory_mb', '?')}MB")
    print(f"  Version: {health.get('version', '?')}")
    
    env = api_get("/gateway/env")
    if "environment" in env:
        print(f"  Environment: {env['environment'].get('type', '?')}")
        print(f"  DB: {env['environment'].get('db', '?')}")
    
    if shutil.which("pm2"):
        os.system("pm2 list | grep aeryn")


def cmd_chat(args):
    """Interactive chat mode."""
    print("💬 Aeryn Chat (type 'quit' to exit)")
    print("─" * 50)
    
    session_id = f"cli_{os.getpid()}"
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        
        result = api_post("/chat", {"goal": user_input, "session_id": session_id})
        
        if "response" in result:
            print(f"\nAeryn: {result['response']}")
            if result.get("tool_used"):
                print(f"  🔧 Tool: {result['tool_used']}")
            if result.get("division"):
                print(f"  📂 Division: {result['division']}")
        elif "error" in result:
            print(f"\n❌ Error: {result['error']}")


def cmd_run(args):
    """Run a single goal."""
    goal = " ".join(args)
    if not goal:
        print("Usage: aeryn run <goal>")
        return
    
    print(f"⚡ Running: {goal}")
    result = api_post("/run", {"goal": goal})
    
    if "response" in result:
        print(f"\n{result['response']}")
    elif "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(json.dumps(result, indent=2))


def cmd_search(args):
    """Search memory/vault."""
    query = " ".join(args)
    if not query:
        print("Usage: aeryn search <query>")
        return
    
    result = api_get(f"/search?q={urllib.parse.quote(query)}")
    if "results" in result:
        print(f"🔍 Found {result['count']} results:")
        for r in result["results"]:
            print(f"  - {r.get('title', 'Untitled')}")
    else:
        print(json.dumps(result, indent=2))


def cmd_tools(args):
    """List registered tools."""
    result = api_get("/plugins")
    if "tools" in result:
        print(f"🔧 {result.get('total_tools', 0)} tools registered:")
        for t in result["tools"]:
            print(f"  - {t['name']}: {t.get('description', '')}")
    else:
        print(json.dumps(result, indent=2))


def cmd_divisions(args):
    """List 5 cognitive divisions."""
    result = api_get("/divisions")
    if "divisions" in result:
        print("📂 5 Cognitive Divisions:")
        divisions = result.get("divisions", [])
        status = result.get("divisions", {})
        for name in divisions:
            info = status.get(name, {})
            print(f"  - {name}: {info.get('agents', 0)} agents, {info.get('pending_tasks', 0)} pending")
    else:
        print(json.dumps(result, indent=2))


def cmd_workflows(args):
    """Manage workflows."""
    result = api_get("/workflows")
    if "workflows" in result:
        wfs = result["workflows"]
        if not wfs:
            print("No workflows. Create one with POST /workflows")
            return
        print(f"📋 {len(wfs)} workflows:")
        for w in wfs:
            print(f"  - {w['name']} ({w['status']})")
    else:
        print(json.dumps(result, indent=2))


def cmd_traces(args):
    """View observability traces."""
    result = api_get("/observability/traces?limit=5")
    if "traces" in result:
        print(f"📊 Recent traces:")
        for t in result["traces"]:
            print(f"  - {t.get('id', '?')}: {t.get('spans', 0)} spans")
    else:
        print(json.dumps(result, indent=2))


def cmd_adapt(args):
    """Trigger self-improvement adaptation."""
    print("🧠 Triggering adaptation...")
    result = api_post("/self-improvement/adapt")
    if "changes" in result:
        print(f"  ✅ {len(result['changes'])} changes applied")
        for c in result["changes"]:
            print(f"    - {c.get('action', '?')}")
    else:
        print(json.dumps(result, indent=2))


def cmd_env(args):
    """Show environment info."""
    result = api_get("/gateway/env")
    print("🌍 Environment:")
    print(json.dumps(result, indent=2))


COMMANDS = {
    "start": cmd_start,
    "stop": cmd_stop,
    "status": cmd_status,
    "chat": cmd_chat,
    "run": cmd_run,
    "search": cmd_search,
    "tools": cmd_tools,
    "divisions": cmd_divisions,
    "workflows": cmd_workflows,
    "traces": cmd_traces,
    "adapt": cmd_adapt,
    "env": cmd_env,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Available commands:", ", ".join(COMMANDS.keys()))
        sys.exit(1)
    
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
