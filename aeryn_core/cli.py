#!/usr/bin/env python3
"""V61.2 — Aeryn CLI: Beautiful, interactive terminal interface.

Usage:
    aeryn                          # Launch interactive mode
    aeryn chat                     # Quick chat
    aeryn run <goal>               # Run a goal
    aeryn status                   # Show status
    aeryn tools                    # List tools
    aeryn divisions                # Show divisions
    aeryn workflows                # Manage workflows
    aeryn traces                   # View traces
    aeryn adapt                    # Trigger self-improvement
    aeryn search <query>           # Search memory
    aeryn env                      # Environment info
    aeryn start|stop               # Manage services
"""
import os
import sys
import json
import shutil
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ── ANSI Colors ──────────────────────────────────────────────
class C:
    R = "\033[0m"; B = "\033[1m"; D = "\033[2m"; U = "\033[4m"
    RED = "\033[91m"; GRN = "\033[92m"; YLW = "\033[93m"; BLU = "\033[94m"
    MAG = "\033[95m"; CYN = "\033[96m"; WHT = "\033[97m"; GRY = "\033[90m"
    BG_BLU = "\033[44m"; BG_GRN = "\033[42m"; BG_RED = "\033[41m"

def color(text, *codes):
    return "".join(codes) + str(text) + C.R

def banner():
    print(color("""
    ╔═══════════════════════════════════════════════════╗
    ║   🤖  A E R Y N  —  AI Agent Platform v61.2     ║
    ║   Adaptive • Self-Improving • Multi-Agent        ║
    ╚═══════════════════════════════════════════════════╝
    """, C.B, C.CYN))

def prompt():
    return color("aeryn", C.B, C.CYN) + color(" › ", C.GRY)

API = os.environ.get("AERYN_API", "http://127.0.0.1:3010")

def api_get(path):
    try:
        with urllib.request.urlopen(f"{API}{path}", timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def api_post(path, data=None):
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(f"{API}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def table(headers, rows):
    """Print a simple table."""
    if not rows:
        print(color("  (empty)", C.GRY))
        return
    widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "  ┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
    mid = "  ├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
    top = "  │" + "│".join(f" {color(h, C.B):{w}} " for h, w in zip(headers, widths)) + "│"
    bot = "  └" + "┴".join("─" * (w + 2) for w in widths) + "┘"
    print(color(sep, C.GRY))
    print(color(top, C.CYN))
    print(color(mid, C.GRY))
    for row in rows:
        line = "  │" + "│".join(f" {str(v):{w}} " for v, w in zip(row, widths)) + "│"
        print(line)
    print(color(bot, C.GRY))

def cmd_status(args):
    """Show service status."""
    h = api_get("/health")
    if "error" in h:
        print(color(f"  ❌ API unreachable: {h['error']}", C.RED))
        return
    env = api_get("/gateway/env")
    print(color("\n  📊 Service Status\n", C.B))
    print(f"  Status:   {color('● ' + h.get('status', '?'), C.GRN if h.get('status') == 'healthy' else C.RED)}")
    print(f"  Memory:   {color(str(h.get('memory_mb', '?')) + ' MB', C.YLW)}")
    print(f"  Version:  {color(h.get('version', '?'), C.CYN)}")
    if "environment" in env:
        print(f"  Env:      {color(env['environment'].get('type', '?'), C.BLU)}")
        print(f"  DB:       {color(env['environment'].get('db', '?'), C.BLU)}")
    print()

def cmd_tools(args):
    """List registered tools."""
    r = api_get("/plugins")
    tools = r.get("tools", [])
    print(color(f"\n  🔧 {len(tools)} Registered Tools\n", C.B))
    for t in tools:
        print(f"  {color(t['name'], C.CYN):20s} {t.get('description', '')}")
        if t.get("tags"):
            print(f"  {'':20s} {color(' '.join(f'#{tag}' for tag in t['tags']), C.GRY)}")
    print()

def cmd_divisions(args):
    """Show 5 cognitive divisions."""
    r = api_get("/divisions")
    divs = r.get("divisions", [])
    icons = {"creative": "🎨", "psych": "🧠", "reasoning": "⚙️", "gov": "🛡️", "infra": "🚀"}
    print(color("\n  🏢 5 Cognitive Divisions\n", C.B))
    for d in divs:
        s = r.get("divisions", {}).get(d, {})
        print(f"  {icons.get(d, '📦')}  {color(d.upper(), C.CYN):12s} {s.get('agents', 0)} agents  {s.get('pending_tasks', 0)} pending")
    print()

def cmd_workflows(args):
    """List workflows."""
    r = api_get("/workflows")
    wfs = r.get("workflows", [])
    print(color(f"\n  📋 {len(wfs)} Workflows\n", C.B))
    if not wfs:
        print(color("  No workflows yet. Create via web dashboard.", C.GRAY))
    for w in wfs:
        status_color = C.GRN if w["status"] == "completed" else C.YLW
        print(f"  {color(w['name'], C.CYN):20s} {color(w['status'], status_color)}")
    print()

def cmd_traces(args):
    """View recent traces."""
    r = api_get("/observability/traces?limit=5")
    traces = r.get("traces", [])
    print(color(f"\n  🔍 Recent Traces ({len(traces)})\n", C.B))
    for t in traces:
        print(f"  {color(t.get('id', '?'), C.CYN):14s} {t.get('spans', 0)} spans")
    print()

def cmd_adapt(args):
    """Trigger self-improvement."""
    print(color("\n  🧠 Triggering adaptation...", C.YLW))
    r = api_post("/self-improvement/adapt")
    changes = r.get("changes", [])
    if changes:
        print(color(f"  ✅ {len(changes)} changes applied:\n", C.GRN))
        for c in changes:
            print(f"    • {c.get('action', '?')}")
    else:
        print(color("  No changes needed. System optimal.", C.GRN))
    print()

def cmd_search(args):
    """Search memory."""
    query = " ".join(args)
    if not query:
        print(color("  Usage: aeryn search <query>", C.YLW))
        return
    r = api_get(f"/search?q={urllib.parse.quote(query)}")
    results = r.get("results", [])
    print(color(f"\n  🔍 '{query}' — {len(results)} results\n", C.B))
    for r in results[:10]:
        print(f"  • {r.get('title', 'Untitled')}")
    print()

def cmd_env(args):
    """Show environment."""
    r = api_get("/gateway/env")
    print(color("\n  🌍 Environment\n", C.B))
    print_json(r)
    print()

def cmd_run(args):
    """Run a single goal."""
    goal = " ".join(args)
    if not goal:
        print(color("  Usage: aeryn run <goal>", C.YLW))
        return
    print(color(f"\n  ⚡ Running: {goal}\n", C.YLW))
    r = api_post("/run", {"goal": goal})
    if "response" in r:
        print(color("  Response:\n", C.B))
        print(f"  {r['response']}\n")
        if r.get("tool_used"):
            print(f"  🔧 Tool: {color(r['tool_used'], C.CYN)}")
        if r.get("division"):
            print(f"  📂 Division: {color(r['division'], C.CYN)}")
    else:
        print(color(f"  ❌ Error: {r.get('error', 'unknown')}", C.RED))
    print()

def cmd_chat(args):
    """Interactive chat mode."""
    print(color("\n  💬 Interactive Chat (type 'quit' to exit)\n", C.B))
    sid = "cli_" + hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    
    while True:
        try:
            user_input = input(prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print(color("\n  👋 Bye!\n", C.CYN))
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print(color("\n  👋 Bye!\n", C.CYN))
            break
        
        r = api_post("/chat", {"goal": user_input, "session_id": sid})
        if "response" in r:
            print(color(f"\n  🤖 {r['response']}", C.GRN))
            if r.get("tool_used"):
                print(color(f"     🔧 {r['tool_used']}  📂 {r.get('division', '—')}", C.GRY))
        elif "error" in r:
            print(color(f"\n  ❌ {r['error']}", C.RED))
        print()

def cmd_interactive(args):
    """Interactive command mode."""
    banner()
    print(color("  Type 'help' for commands, 'quit' to exit.\n", C.GRY))
    
    while True:
        try:
            cmd_line = input(prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print(color("\n  👋 Bye!\n", C.CYN))
            break
        if not cmd_line:
            continue
        
        parts = cmd_line.split()
        cmd = parts[0].lower()
        rest = parts[1:]
        
        if cmd in ("quit", "exit", "q"):
            print(color("\n  👋 Bye!\n", C.CYN))
            break
        elif cmd == "help":
            print(color("""
  Commands:
    chat              Interactive chat mode
    run <goal>        Run a single goal
    status            Show service status
    tools             List registered tools
    divisions         Show 5 cognitive divisions
    workflows         List workflows
    traces            View recent traces
    adapt             Trigger self-improvement
    search <query>    Search memory
    env               Show environment info
    help              Show this help
    quit              Exit
            """, C.CYN))
        elif cmd == "chat":
            cmd_chat([])
            break
        elif cmd == "run":
            cmd_run(rest)
        elif cmd == "status":
            cmd_status(rest)
        elif cmd == "tools":
            cmd_tools(rest)
        elif cmd == "divisions":
            cmd_divisions(rest)
        elif cmd == "workflows":
            cmd_workflows(rest)
        elif cmd == "traces":
            cmd_traces(rest)
        elif cmd == "adapt":
            cmd_adapt(rest)
        elif cmd == "search":
            cmd_search(rest)
        elif cmd == "env":
            cmd_env(rest)
        else:
            print(color(f"  Unknown: {cmd}. Type 'help'.", C.YLW))

COMMANDS = {
    "interactive": cmd_interactive,
    "chat": cmd_chat,
    "run": cmd_run,
    "status": cmd_status,
    "tools": cmd_tools,
    "divisions": cmd_divisions,
    "workflows": cmd_workflows,
    "traces": cmd_traces,
    "adapt": cmd_adapt,
    "search": cmd_search,
    "env": cmd_env,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_interactive(sys.argv[1:])
    else:
        COMMANDS[sys.argv[1]](sys.argv[2:])

if __name__ == "__main__":
    main()
