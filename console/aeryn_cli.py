#!/data/data/com.termux/files/home/aeryn-venv/bin/python
"""V61.3 — Aeryn CLI/TUI: aksesibilitas ala Hermes dari terminal.

V62.26_CLI_TUI_UPGRADE
CLI : aeryn status|goals|goal-add|chat|pursue|obs|services|watch
        |ledger|sensor|matter|briefing|horizon|cost   (RM4-RM10)
TUI : aeryn tui   (dashboard terminal — rich live-refresh + panel
        keuangan/cuaca/scheduler/cost + slash commands)
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
                # V62.26: panel baru (keuangan + cuaca + scheduler + cost)
                try:
                    led = _get("/ledger/balance")
                    led_txt = (f"Rp {led.get('balance', 0):,.0f}")
                except Exception:
                    led_txt = "—"
                try:
                    wthr = _get("/sensor/weather")
                    wthr_txt = (f"{wthr.get('temperature_c', '?')}°C "
                                f"{wthr.get('condition', '')}")
                except Exception:
                    wthr_txt = "—"
                try:
                    sch = _get("/scheduler/health")
                    sch_txt = (f"{'●' if sch.get('running') else '○'} "
                               f"{sch.get('tick_count', 0)} ticks")
                except Exception:
                    sch_txt = "—"
                try:
                    cst = _get("/cost")
                    cst_txt = f"${cst.get('spend', {}).get('estimate_usd', 0):.2f}"
                except Exception:
                    cst_txt = "—"
                c.print(Columns([
                    Panel(f"[bold]{h.get('status')}[/]\n{h.get('memory_mb', 0)} MB",
                          title="api", border_style="green"),
                    Panel(f"{reqs.get('total', 0)} req\nerr {reqs.get('error_rate', 0)}%",
                          title="24h", border_style="blue"),
                    Panel(f"{st.get('active', 0)} aktif\n{st.get('completed', 0)} selesai",
                          title="goals", border_style="magenta"),
                    Panel(f"[bold]{led_txt}[/]", title="keuangan",
                          border_style="yellow"),
                    Panel(wthr_txt, title="cuaca", border_style="cyan"),
                    Panel(sch_txt, title="scheduler", border_style="green"),
                    Panel(cst_txt, title="cost", border_style="red"),
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
            # V62.26: slash commands (Hermes-style) — input TUI interaktif
            try:
                import select
                import termios
                old_attrs = termios.tcgetattr(sys.stdin)
                # non-blocking input check (5s refresh tetap jalan)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline().strip()
                    if line.startswith("/"):
                        _tui_slash(c, line[1:])
                    elif line:
                        _tui_chat(c, line)
            except (termios.error, ImportError):
                pass  # bukan TTY — refresh saja
            time.sleep(5)
    except KeyboardInterrupt:
        c.print("\n[dim]sampai jumpa~[/]")
    return 0


def _tui_chat(c, message: str) -> None:
    """Chat via /v1/chat (agent loop penuh) — fallback /chat."""
    try:
        r = _post("/v1/chat", {"message": message, "session_id": "aeryn-tui",
                               "user_id": "sen"})
        out = r.get("content") or r.get("response") or ""
        c.print(f"  [bold cyan]Aeryn[/] {out[:600]}")
    except Exception:
        try:
            r = _post("/chat", {"goal": message, "session_id": "aeryn-tui"})
            c.print(f"  [bold cyan]Aeryn[/] {r.get('response', '')[:600]}")
        except Exception as e:
            c.print(f"  [red]chat gagal: {e}[/]")


def _tui_slash(c, cmd: str) -> None:
    """Slash commands TUI (Hermes-style): /status /cost /ledger /sensor
    /briefing /horizon /matter /help."""
    parts = cmd.split()
    name = parts[0].lower() if parts else "help"
    try:
        if name == "help":
            c.print("[dim]  /chat <pesan> /status /cost /ledger /sensor "
                    "/briefing /horizon <goal> /matter <teks> /help[/]")
        elif name == "status":
            h = _get("/health")
            c.print(f"  ● {h.get('status')} · {h.get('memory_mb', 0)} MB")
        elif name == "cost":
            r = _get("/cost")
            c.print(f"  💰 ${r.get('spend', {}).get('estimate_usd', 0):.4f} est")
        elif name == "ledger":
            r = _get("/ledger/balance")
            c.print(f"  💵 Rp {r.get('balance', 0):,.0f}")
        elif name == "sensor":
            sub = parts[1] if len(parts) > 1 else "weather"
            r = _get(f"/sensor/{sub}")
            if sub == "weather":
                c.print(f"  🌤️  {r.get('temperature_c', '?')}°C {r.get('condition', '')}")
            else:
                c.print(f"  📅 {r.get('count', '?')} upcoming")
        elif name == "briefing":
            r = _get("/briefing/preview")
            c.print(f"  🌅 {str(r)[:400]}")
        elif name == "horizon":
            goal = " ".join(parts[1:])
            if not goal:
                c.print("  [dim]pakai: /horizon <goal>[/]")
            else:
                r = _post("/horizon/plan", {"goal": goal})
                c.print(f"  🗺️  task {r.get('task_id')} "
                        f"({r.get('steps', 0)} langkah)")
        elif name == "matter":
            text = " ".join(parts[1:])
            if not text:
                c.print("  [dim]pakai: /matter <teks>[/]")
            else:
                r = _post("/matter", {"text": text})
                c.print(f"  ⭐ {str(r)[:200]}")
        else:
            c.print(f"  [yellow]unknown /{name} — /help[/]")
    except Exception as e:
        c.print(f"  [red]/{name} gagal: {e}[/]")


# ─────────────────────────────────────────────────────────────

def _post(path: str, data: dict):
    """POST JSON ke API Aeryn."""
    req = urllib.request.Request(API + path,
                                 data=json.dumps(data).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


# ── V62.26: CLI commands baru (RM4-RM10) ──

def cmd_ledger(args):
    """Ledger: balance (default) / report."""
    sub = args[0] if args else "balance"
    if sub == "report":
        r = _get("/ledger/report")
        print(f"\n  Masuk : Rp {r.get('income', 0):,.0f}")
        print(f"  Keluar: Rp {r.get('expense', 0):,.0f}")
        print(f"  Saldo : Rp {r.get('balance', 0):,.0f}\n")
    else:
        r = _get("/ledger/balance")
        print(f"\n  💵 Saldo: Rp {r.get('balance', 0):,.0f}\n")


def cmd_sensor(args):
    """Sensor: weather (default) / calendar / location."""
    sub = args[0] if args else "weather"
    r = _get(f"/sensor/{sub}")
    if sub == "weather":
        print(f"\n  🌤️  {r.get('temperature_c', '?')}°C · {r.get('condition', '')}"
              f" · humidity {r.get('humidity', '?')}%\n")
    elif sub == "calendar":
        for it in (r.get("items") or [])[:10]:
            print(f"  📅 {it.get('when', '?'):20s} {it.get('what', '?')[:50]}")
        print()
    else:
        print(json.dumps(r, indent=2, ensure_ascii=False))


def cmd_matter(args):
    """Tell Aeryn what matters — goal + fact tercatat (proactive-goal)."""
    text = " ".join(args)
    if not text:
        print("pakai: aeryn matter <teks>")
        return 1
    r = _post("/matter", {"text": text})
    print(f"\n  ⭐ {json.dumps(r, ensure_ascii=False)[:300]}\n")
    return 0


def cmd_briefing(args):
    """Briefing pagi (preview)."""
    r = _get("/briefing/preview")
    print("\n  🌅 BRIEFING\n")
    print("  " + json.dumps(r, indent=2, ensure_ascii=False)[:1500].replace("\n", "\n  "))
    print()


def cmd_horizon(args):
    """Long-horizon: plan <goal> / status <task_id> / execute <task_id>."""
    if not args:
        print("pakai: aeryn horizon plan|status|execute <arg>")
        return 1
    sub, rest = args[0], args[1:]
    if sub == "plan":
        goal = " ".join(rest)
        if not goal:
            print("pakai: aeryn horizon plan <goal>")
            return 1
        r = _post("/horizon/plan", {"goal": goal})
        print(f"\n  🗺️  task {r.get('task_id')} · {r.get('steps', 0)} langkah\n")
    elif sub == "status":
        r = _get(f"/horizon/status/{rest[0]}")
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1200])
    elif sub == "execute":
        r = _post(f"/horizon/execute/{rest[0]}", {})
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1200])
    else:
        print(f"unknown horizon sub: {sub}")
        return 1
    return 0


def cmd_cost(args):
    """Cost tracking (dari spans nyata)."""
    r = _get("/cost")
    print(f"\n  💰 Cost estimate: ${r.get('spend', {}).get('estimate_usd', 0):.4f}\n")


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
    # V62.26: commands baru (RM4-RM10)
    if cmd == "ledger":
        return cmd_ledger(rest)
    if cmd == "sensor":
        return cmd_sensor(rest)
    if cmd == "matter":
        return cmd_matter(rest)
    if cmd == "briefing":
        return cmd_briefing(rest)
    if cmd == "horizon":
        return cmd_horizon(rest)
    if cmd == "cost":
        return cmd_cost(rest)
    print(f"perintah tak dikenal: {cmd} — pakai: aeryn help")
    return 1


if __name__ == "__main__":
    sys.exit(main())
