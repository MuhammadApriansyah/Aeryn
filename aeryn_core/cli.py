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
    """Show service status (unified_status — SATU sumber kebenaran)."""
    try:
        from aeryn_core.utils.unified_status import get_full_status, format_cli
        s = get_full_status()
        # Tambah memory MB dari API kalau reachable
        h = api_get("/health")
        if "memory_mb" in h:
            print(format_cli(s).replace(
                f"Version:  v{s['version']}",
                f"Version:  v{s['version']}  ·  Memory: {h['memory_mb']} MB"
            ))
        else:
            print(format_cli(s))
    except Exception as e:
        print(color(f"  ⚠️ unified_status gagal: {e} — fallback API", C.YLW))
        h = api_get("/health")
        if "error" in h:
            print(color(f"  ❌ API unreachable: {h['error']}", C.RED))
            return
        print(color("\n  📊 Service Status\n", C.B))
        print(f"  Status: {h.get('status', '?')}")

def cmd_tools(args):
    """List registered tools (dari plugin_registry — sumber yang sama dgn chat)."""
    try:
        from aeryn_core.platform.plugin_registry import get_registry
        tools = get_registry().list_tools()
        print(color(f"\n  🔧 {len(tools)} Registered Tools\n", C.B))
        for t in tools:
            print(f"  {color(t['name'], C.CYN):20s} {t.get('description', '')[:70]}")
            if t.get("tags"):
                print(f"  {'':20s} {color(' '.join(f'#{tag}' for tag in t['tags'][:4]), C.GRY)}")
        print()
    except Exception as e:
        print(color(f"  ⚠️ registry gagal: {e}", C.YLW))



def cmd_services(args):
    """Status semua service runit (api, worker, watchdog, redis, postgres)."""
    try:
        from aeryn_core.utils.unified_status import get_services
        print(color("\n  ⚙️ Services\n", C.B))
        for s in get_services():
            icon = C.GRN + "●" if s["status"] == "up" else C.RED + "○"
            print(f"  {icon} {s['name']}: {s['status']}")
        print()
    except Exception as e:
        print(color(f"  ⚠️ {e}", C.YLW))


def cmd_watch(args):
    """Tail watchdog log (monitoring live)."""
    import subprocess
    home = os.environ.get("HOME", "")
    log = os.path.join(home, "tmp", "aeryn-watchdog.log")
    if not os.path.exists(log):
        print(color("  ⚠️ Watchdog log belum ada: " + log, C.YLW))
        return
    try:
        out = subprocess.run(["tail", "-20", log], capture_output=True, text=True, timeout=10)
        print(color("\n  🐕 Watchdog (20 terakhir)\n", C.B))
        for line in (out.stdout or "").strip().split("\n")[-20:]:
            print(f"  {line}")
        print()
    except Exception as e:
        print(color(f"  ⚠️ {e}", C.YLW))



def cmd_welcome(args):
    """Tur 3 langkah untuk pengguna awam — coba tanya, minta, cek hasil."""
    print(color("\n  👋 Selamat datang di Aeryn!\n", C.B))
    print("  Aku asisten AI yang hidup di HP ini. Aku bisa ngobrol,")
    print("  ingat preferensi kamu, cek kondisi HP, dan bantu kerjaan.")
    print()
    print(color("  Tur 3 langkah (coba langsung):\n", C.YLW))
    print(color("  1️⃣  Ngobrol biasa:", C.CYN))
    print("       aeryn chat    → lalu ketik apa saja, mis: \"halo, kamu bisa apa?\"")
    print()
    print(color("  2️⃣  Minta aku nyatat/ingetin (aku simpan beneran):", C.CYN))
    print("       aeryn chat    → \"catat ya, aku suka kopi susu gula aren\"")
    print("       aeryn chat    → \"ingetin besok pagi buat minum air\"")
    print()
    print(color("  3️⃣  Cek kondisi & hasil:", C.CYN))
    print("       aeryn status  → kesehatan sistem (5 services)")
    print("       aeryn tools   → daftar kemampuanku")
    print("       aeryn search redis → cari di memoriku")
    print()
    print(color("  Tips: ketik help untuk semua perintah. Mulai dari nomor 1 ya!\n", C.GRY))
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
    """Search memory (memory library RAG — sumber yang sama dgn agent tools)."""
    query = " ".join(args)
    if not query:
        print(color("  Usage: aeryn search <query>", C.YLW))
        return
    try:
        from aeryn_core.platform.internal_tools import tool_memory_search
        r = tool_memory_search(query, limit=5)
        n = r.get("ok") and r.get("output", "").count("###") or 0
        print(color(f"\n  🔍 '{query}' — {n} results\n", C.B))
        if r.get("ok"):
            print("  " + r.get("output", "")[:1500].replace("\n", "\n  "))
        else:
            print(color(f"  {r.get('error', 'no results')}", C.GRY))
        print()
    except Exception as e:
        print(color(f"  ⚠️ memory search gagal: {e}", C.YLW))

def cmd_env(args):
    """Show environment (unified_status — deteksi NYATA, bukan stale)."""
    try:
        from aeryn_core.utils.unified_status import detect_environment, get_version
        env = detect_environment()
        print(color("\n  🌍 Environment\n", C.B))
        print(f"  Type:    {env['type']}")
        print(f"  DB:      {env['db']}")
        print(f"  Version: v{get_version()}")
        print()
    except Exception as e:
        print(color(f"  ⚠️ {e}", C.YLW))
        r = api_get("/gateway/env")
        print_json(r)

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
    print(color("  Type 'help' for commands, 'quit' to exit.", C.GRY))

    # TUI_PANEL_SHOWN — rich status panel (live dari unified_status)
    try:
        from aeryn_core.utils.unified_status import get_full_status
        s = get_full_status()
        s_icon = {"healthy": "●", "degraded": "◐", "down": "○"}.get(s["status"], "○")
        print(color(f"  {s_icon} {s['status']} · v{s['version']} · {s['env']['type']} · {s['env']['db']}", C.GRY))
        print(color(f"  🔧 {s['tools']} tools · ⚡ {s['skills']} skills · " +
                    " ".join(("●" if x["status"] == "up" else "○") + x["name"].replace("aeryn-", "") for x in s["services"]), C.GRY))
        print()
    except Exception:
        pass
    
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
    status            Service + tools + skills (satu layar)
    tools             List registered tools (live dari registry)
    services          Status semua service runit
    watch             Tail watchdog log (monitoring live)
    welcome           Tur 3 langkah untuk pemula
    divisions         Show 5 cognitive divisions
    workflows         List workflows
    traces            View recent traces
    adapt             Trigger self-improvement
    search <query>    Search memory (RAG real)
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

def cmd_goals(args):
    """List niat (goals) Aeryn — aktif saja, urut prioritas."""
    r = api_get("/goals")
    goals = r.get("goals", [])
    active = [g for g in goals if g.get("status", "active") != "completed"]
    print(color(f"\n  🎯 Niat Aktif ({len(active)})\n", C.B))
    if not active:
        print(color("  (belum ada niat — aeryn run <goal> untuk mulai)", C.GRY))
    for g in active[:10]:
        prog = g.get("progress", 0)
        bar = "█" * (prog // 10) + "░" * (10 - prog // 10)
        print(f"  {color(g.get('title', '?')[:40], C.CYN):42s} {bar} {prog}%")
    print()
def cmd_skill(args):
    """Skill ecosystem: add <nama> / list."""
    if not args or args[0] == "list":
        try:
            from aeryn_core.skills.skill_installer import skill_list
            r = skill_list()
            print(color(f"\n  ⚡ Ter-install ({len(r['installed'])})\n", C.B))
            for s in r["installed"]:
                print(f"  • {s}")
            print(color(f"\n  📦 Katalog tersedia ({len(r['catalog'])})\n", C.B))
            for s in r["catalog"]:
                print(f"  • {s}  (aeryn skill add " + s + ")")
            print()
        except Exception as e:
            print(color(f"  ⚠️ {e}", C.YLW))
        return
    if args[0] == "add" and len(args) > 1:
        try:
            from aeryn_core.skills.skill_installer import skill_add
            r = skill_add(" ".join(args[1:]))
            if r.get("ok"):
                print(color(f"\n  ✅ Skill '{r['skill']}' ter-install ({r['source']})\n", C.GRN))
            else:
                print(color(f"\n  ❌ {r.get('error', 'gagal')}\n", C.RED))
        except Exception as e:
            print(color(f"  ⚠️ {e}", C.YLW))
        return
    print(color("  Usage: aeryn skill add <nama> | aeryn skill list", C.YLW))
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
    "services": cmd_services,
    "welcome": cmd_welcome,
    "goals": cmd_goals,
    "skill": cmd_skill,
    "watch": cmd_watch,
}





def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_interactive(sys.argv[1:])
    else:
        COMMANDS[sys.argv[1]](sys.argv[2:])

if __name__ == "__main__":
    main()
