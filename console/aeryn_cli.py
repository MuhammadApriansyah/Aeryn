#!/data/data/com.termux/files/home/aeryn-venv/bin/python
"""V61.3 — Aeryn CLI/TUI: aksesibilitas ala Hermes dari terminal.

CLI : aeryn status|goals|goal-add|chat|pursue|obs|services|watch
TUI : aeryn tui   (dashboard terminal — rich live-refresh)
Semua via API Aeryn (127.0.0.1:3010) — konsisten dgn skill aeryn-control.
"""
import json
import sys
import os
import time
import urllib.request

API = os.environ.get("AERYN_API", "http://127.0.0.1:3010")
TIMEOUT = 10


def _get(path: str):
    with urllib.request.urlopen(API + path, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _post(path: str, params: dict | None = None):
    import urllib.parse
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


# ─────────────────────────────────────────────────────────────
# CLI commands
# ─────────────────────────────────────────────────────────────

def cmd_status():
    try:
        h = _get("/health")
        obs = _get("/v1/obs/summary?window_hours=24")
    except Exception as e:
        print(f"aeryn: TIDAK TERJANGKAU ({e})")
        return 1
    from rich.console import Console
    from rich.table import Table
    c = Console()
    c.print(f"[bold cyan]Aeryn[/] v{h.get('version')} — {h.get('status')}")
    t = Table(show_header=False, box=None, pad_edge=False)
    t.add_row("memori", f"{h.get('memory_mb', 0)} MB")
    reqs = obs.get("requests") or {}
    facts = obs.get("facts") or {}
    cron = obs.get("cron") or {}
    if not isinstance(reqs, dict):
        reqs = {}
    if not isinstance(facts, dict):
        facts = {"total": facts}
    if not isinstance(cron, dict):
        cron = {"total": cron}
    t.add_row("requests 24h", f"{reqs.get('total', 0)} (err {reqs.get('error_rate', 0)}%)")
    t.add_row("facts", str(facts.get('total', facts if facts else '?')))
    t.add_row("cron", str(cron.get('total', cron if cron else '?')))
    c.print(t)
    subs = obs.get("subsystems") or {}
    if not isinstance(subs, dict):
        subs = {}
    line = "  ".join(
        f"[green]{k}[/]" if (v or {}).get("status") == "healthy"
        else f"[yellow]{k}[/]" if (v or {}).get("status") == "degraded"
        else f"[red]{k}[/]"
        for k, v in subs.items()) if subs else "[dim]—[/]"
    c.print(f"subsistem: {line}")
    return 0


def cmd_goals(status: str = ""):
    d = _get("/v1/agents/goals" + (f"?status={status}" if status else ""))
    from rich.console import Console
    from rich.table import Table
    c = Console()
    st = d.get("stats", {})
    c.print(f"[bold]Goals[/] — aktif {st.get('active', 0)} · selesai "
            f"{st.get('completed', 0)} · rate {st.get('completion_rate', 0)}")
    t = Table()
    t.add_column("id", style="dim")
    t.add_column("title")
    t.add_column("prio", justify="right")
    t.add_column("progress", justify="right")
    t.add_column("status")
    for g in d.get("goals", []):
        pr = g.get("progress", 0)
        pcol = "[green]" + str(pr) + "%" if pr >= 100 else str(pr) + "%"
        t.add_row(g["id"][:8], g["title"][:40], str(g.get("priority", 5)),
                  pcol, g.get("status", "?"))
    c.print(t)
    return 0


def cmd_goal_add(title: str, steps: str = "", priority: int = 5):
    r = _post("/v1/agents/goals", {"title": title, "steps": steps,
                                   "priority": priority})
    if r.get("ok"):
        print(f"goal dibuat: {r['id']} — {r['title']}")
        if r.get("steps"):
            print(f"  langkah: {' → '.join(r['steps'])}")
        return 0
    print(f"gagal: {r.get('error')}")
    return 1


def cmd_pursue():
    r = _post("/v1/agents/goals/pursue")
    p = r.get("pursued")
    if p:
        print(f"mengejar: {p['title']} — langkah '{p['step']}' "
              f"→ {p['progress']}%" + (" ✓ selesai" if p.get("done") else ""))
        return 0
    print("tak ada goal aktif — aeryn idle (maintenance)")
    return 0


def cmd_chat(message: str, session_id: str = "cli"):
    import urllib.parse
    url = (f"{API}/v1/chat/stream?session_id={session_id}&user_id=cli")
    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        for raw in r:
            line = raw.decode("utf-8", errors="ignore").strip()
            if line.startswith("data: "):
                try:
                    ev = json.loads(line[6:])
                except (ValueError, TypeError):
                    continue
                if ev.get("type") == "token":
                    print(ev.get("content", ""), end="", flush=True)
                elif ev.get("type") == "message_complete":
                    print()
    return 0


def cmd_obs():
    cmd_status()
    return 0


def cmd_services():
    from rich.console import Console
    from rich.table import Table
    c = Console()
    t = Table()
    t.add_column("service")
    t.add_column("status")
    for name in ("aeryn-api", "postgres", "sshd"):
        try:
            h = _get("/health") if name == "aeryn-api" else {"status": "?"}
        except Exception:
            h = {"status": "down"}
        label = {"healthy": "[green]run[/]", "down": "[red]down[/]"}.get(
            h.get("status"), "[yellow]?[/]")
        t.add_row(name, label)
    c.print(t)
    c.print("[dim]supervised runit (runsvdir) — auto-restart + auto-boot[/]")
    return 0


def cmd_watch(interval: int = 5):
    """Live-refresh status (mini-TUI loop)."""
    from rich.console import Console
    c = Console()
    try:
        while True:
            c.clear()
            c.print("[dim]aeryn watch — Ctrl+C keluar[/]\n")
            cmd_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        c.print("\n[dim]keluar[/]")
    return 0


def cmd_tui():
    """Dashboard terminal (rich) — status + goals + services + chat."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.columns import Columns
    c = Console()
    try:
        while True:
            c.clear()
            c.print(Panel.fit(
                "[bold cyan]AERYN[/] — Autonomous AI Agent · [dim]TUI "
                "(Ctrl+C keluar · perintah: /chat <pesan>)[/]",
                border_style="cyan"))
            try:
                h = _get("/health")
                obs = _get("/v1/obs/summary?window_hours=24")
                g = _get("/v1/agents/goals")
                subs = obs.get("subsystems") or {}
                if not isinstance(subs, dict):
                    subs = {}
                reqs = obs.get("requests") or {}
                if not isinstance(reqs, dict):
                    reqs = {}
                st = g.get("stats") or {}
                if not isinstance(st, dict):
                    st = {}
                c.print(Columns([
                    Panel(f"[bold]{h.get('status')}[/]\n{h.get('memory_mb', 0)} MB",
                          title="api", border_style="green"),
                    Panel(f"{reqs.get('total', 0)} req\nerr {reqs.get('error_rate', 0)}%",
                          title="24h", border_style="blue"),
                    Panel(f"{st.get('active', 0)} aktif\n{st.get('completed', 0)} selesai",
                          title="goals", border_style="magenta"),
                ]))
                line = "  ".join(
                    f"[green]{k}[/]" if (v or {}).get("status") == "healthy"
                    else f"[yellow]{k}[/]"
                    for k, v in subs.items()) if subs else "[dim]—[/]"
                c.print(f"subsistem: {line}")
                if g.get("goals"):
                    nxt = g["goals"][0]
                    c.print(f"[dim]niat berikutnya:[/] {nxt['title']} "
                            f"({nxt.get('progress', 0)}%)")
            except Exception as e:
                c.print(f"[red]api tak terjangkau: {e}[/]")
            time.sleep(5)
    except KeyboardInterrupt:
        c.print("\n[dim]sampai jumpa~[/]")
    return 0


# ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]
    if cmd == "status":
        return cmd_status()
    if cmd == "goals":
        return cmd_goals(rest[0] if rest else "")
    if cmd == "goal-add":
        if not rest:
            print("pakai: aeryn goal-add <title> [steps=koma] [priority]")
            return 1
        steps = ""
        prio = 5
        for a in rest[1:]:
            if a.startswith("steps="):
                steps = a[6:]
            elif a.isdigit():
                prio = int(a)
        return cmd_goal_add(rest[0], steps, prio)
    if cmd == "pursue":
        return cmd_pursue()
    if cmd == "chat":
        if not rest:
            print("pakai: aeryn chat <pesan>")
            return 1
        return cmd_chat(" ".join(rest))
    if cmd == "obs":
        return cmd_obs()
    if cmd == "services":
        return cmd_services()
    if cmd == "watch":
        return cmd_watch(int(rest[0]) if rest and rest[0].isdigit() else 5)
    if cmd == "tui":
        return cmd_tui()
    print(f"perintah tak dikenal: {cmd} — pakai: aeryn help")
    return 1


if __name__ == "__main__":
    sys.exit(main())
