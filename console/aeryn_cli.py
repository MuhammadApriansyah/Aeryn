#!/data/data/com.termux/files/home/aeryn-venv/bin/python
"""Aeryn CLI/TUI v63 — REWRITE penuh meniru Hermes.

Source: console/aeryn_cli.py (di-replace penuh).

Visual (dari Hermes skin default — gold & kawaii):
- Banner ╔═╗ gold + braille hippo art + tools/skills summary (build_welcome_banner)
- Prompt ❯ + input rule ═══ gold (Hermes input_rule #CD7F32)
- Response border gold (#FFD700), status bar bg #1a1a2e + text #C0C0C0
  + strong #FFD700 (model · context · session · duration · battery)
- Rich console dengan warna skin persis Hermes

Command set (dari Hermes COMMANDS_BY_CATEGORY — 5 kategori):
- Session (12): /new /history /save /retry /goals /goal /steer /status
  /tasks /workflows /traces /matter
- Configuration (8): /config /model /approvals /timestamps /verbose
  /scheduler /sensor /cost
- Info (7): /whoami /profile /help /version /env /services /briefing
- Tools & Skills (6): /tools /skills /memory /horizon /learning /search
- Exit (2): /quit /exit

TUI (prompt_toolkit — fixed input area, seperti Hermes):
- Input area bawah (prompt ❯ + buffer) + patch_stdout (response stream
  tidak merusak layout) + InMemoryHistory (arrow-up recall)
- Slash command completion menu (seperti Hermes completion_menu_bg)
- Status bar bawah: ⚕ model · session · goal · duration (Hermes-style)
Idempoten via marker V63.
"""

import json
import os
import re
import shutil
import sys
import time
import urllib.request
from urllib.parse import quote as _urlquote
from datetime import datetime

API = os.environ.get("AERYN_API", "http://127.0.0.1:3010")
TIMEOUT = 10

__version__ = "63"
__release_date__ = "2026.9.24"

# ── Skin Hermes (default — gold & kawaii) ──
SKIN = {
    "banner_border": "#CD7F32",
    "banner_title": "#FFD700",
    "banner_accent": "#FFBF00",
    "banner_dim": "#B8860B",
    "banner_text": "#FFF8DC",
    "ui_accent": "#FFBF00",
    "ui_label": "#DAA520",
    "ui_ok": "#4caf50",
    "ui_error": "#ef5350",
    "ui_warn": "#ffa726",
    "prompt": "#FFF8DC",
    "input_rule": "#CD7F32",
    "response_border": "#FFD700",
    "status_bar_bg": "#1a1a2e",
    "status_bar_text": "#C0C0C0",
    "status_bar_strong": "#FFD700",
    "status_bar_dim": "#8A7A4A",
    "status_bar_good": "#8FBC8F",
}
PROMPT_SYMBOL = "❯"
AGENT_NAME = "Aeryn"
WELCOME = "Selamat datang di Aeryn! Ketik pesan atau /help untuk commands."

# Braille hippo (Hermes banner_logo — dari skin default)
HIPPO_ART = [
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⣀⣀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⢀⣠⣴⣾⣿⣿⣇⠸⣿⣿⠇⣸⣿⣿⣷⣦⣄⡀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⢀⣠⣴⣶⠿⠋⣩⡿⣿⡿⠻⣿⡇⢠⡄⢸⣿⠟⢿⣿⢿⣍⠙⠿⣶⣦⣄⡀⠀",
    "⠀⠀⠉⠉⠁⠶⠟⠋⠀⠉⠀⢀⣈⣁⡈⢁⣈⣁⡀⠀⠉⠀⠙⠻⠶⠈⠉⠉⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⡿⠛⢁⡈⠛⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⣦⣤⣈⠁⢠⣴⣿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣴⠦⠈⠙⠿⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣤⡈⠁⢤⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
]

# ── Command set (Hermes COMMANDS_BY_CATEGORY — adaptasi Aeryn) ──
# (name, description, args_hint, handler_fn_name)
COMMANDS_BY_CATEGORY = {
    "Session": [
        ("/new", "Sesi baru (reset konteks chat)", "", "cmd_new"),
        ("/history", "Riwayat chat sesi ini", "[n]", "cmd_history"),
        ("/save", "Simpan konteks (handoff untuk sesi berikut)", "", "cmd_save"),
        ("/retry", "Ulangi pesan terakhir", "", "cmd_retry"),
        ("/goals", "Niat aktif (progress bar)", "", "cmd_goals_cmd"),
        ("/goal", "Detail niat", "[id]", "cmd_goal_detail"),
        ("/steer", "Arahkan niat yang jalan", "[id] <pesan>", "cmd_steer"),
        ("/status", "Status goals + services", "", "cmd_status_cmd"),
        ("/tasks", "A2A tasks (subagent + supervisor)", "", "cmd_tasks"),
        ("/workflows", "Workflows (goal-derived)", "", "cmd_workflows_cmd"),
        ("/traces", "Traces (OTel observability)", "[n]", "cmd_traces_cmd"),
        ("/matter", "Tell Aeryn what matters (proactive-goal)", "<teks>", "cmd_matter_cmd"),
    ],
    "Configuration": [
        ("/config", "Konfigurasi Aeryn (gateway/env)", "", "cmd_config"),
        ("/model", "Model aktif + provider", "", "cmd_model"),
        ("/approvals", "Approval queue (HITL governance)", "", "cmd_approvals"),
        ("/timestamps", "Toggle timestamp [HH:MM] di messages", "[on|off]", "cmd_timestamps"),
        ("/verbose", "Toggle verbose output (tool + division)", "[on|off]", "cmd_verbose"),
        ("/scheduler", "Scheduler health (Rust native)", "", "cmd_scheduler_cmd"),
        ("/sensor", "Sensor dunia: weather/calendar/location", "[sub]", "cmd_sensor_cmd"),
        ("/cost", "Cost estimate (dari spans nyata)", "", "cmd_cost_cmd"),
    ],
    "Info": [
        ("/whoami", "Identitas Aeryn (AGENT_IDENTITY)", "", "cmd_whoami"),
        ("/profile", "Profil sesi + user", "", "cmd_profile"),
        ("/help", "Available Commands (kategorikal)", "[query]", "cmd_help"),
        ("/version", "Versi Aeryn (v63)", "", "cmd_version"),
        ("/env", "Environment info", "", "cmd_env_cmd"),
        ("/services", "Status semua service runit", "", "cmd_services_cmd"),
        ("/briefing", "Briefing pagi (preview)", "", "cmd_briefing_cmd"),
    ],
    "Tools & Skills": [
        ("/tools", "Registered tools (live dari API)", "", "cmd_tools_cmd"),
        ("/skills", "Skills ecosystem", "[list|add]", "cmd_skills_cmd"),
        ("/memory", "Memory search (RAG real)", "<query>", "cmd_memory_cmd"),
        ("/horizon", "Long-horizon: plan/status/execute", "<sub> <arg>", "cmd_horizon_cmd"),
        ("/learning", "Learning: status/consolidate", "[sub]", "cmd_learning_cmd"),
        ("/search", "Search memory (alias /memory)", "<query>", "cmd_memory_cmd"),
    ],
    "Exit": [
        ("/quit", "Keluar", "", "cmd_quit"),
        ("/exit", "Keluar (alias /quit)", "", "cmd_quit"),
    ],
}


def _all_commands():
    out = {}
    for cat, cmds in COMMANDS_BY_CATEGORY.items():
        for c in cmds:
            out[c[0]] = (cat, c[1], c[2], c[3])
    return out


ALL_COMMANDS = _all_commands()

# ── ANSI helpers (skin Hermes) ──

def _c(code: str) -> str:
    return f"\x1b[{code}m"


def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)};{int(h[2:4], 16)};{int(h[4:6], 16)}"


def _fg(hex_color: str) -> str:
    return f"\x1b[38;2;{_hex_rgb(hex_color)}m"


BOLD = _c("1")
DIM = _c("2")
RST = _c("0")


def _print(text: str = "") -> None:
    print(text)


def _fmt_label(cmd: str, desc: str) -> str:
    """Baris command help (Hermes-style: cmd accent bold + desc dim)."""
    return f"    {BOLD}{_fg(SKIN['ui_accent'])}{cmd:<14}{RST} {DIM}-{RST} {desc}"


# ── API helpers ──

def _set_api(url: str) -> None:
    """Override API base URL (dipakai main() --api)."""
    global API
    API = url


def _get(path: str, timeout: float = TIMEOUT):
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        return json.loads(r.read())


def _post(path: str, data: dict, timeout: float = 120):
    req = urllib.request.Request(API + path,
                                 data=json.dumps(data).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# ── Banner (Hermes-style: ╔═╗ gold + hippo + summary) ──

def build_banner() -> str:
    w = min(shutil.get_terminal_size().columns - 2, 88)
    if w < 30:
        return f"\n{_fg(SKIN['banner_title'])}{AGENT_NAME} v{__version__}{RST} {_fg(SKIN['banner_dim'])}- Self-Hosted Personal AI System{RST}\n"
    bar = "═" * w
    out = [
        f"\n{BOLD}{_fg(SKIN['banner_border'])}╔{bar}╗{RST}",
    ]
    # Line 1: nama + versi
    line1 = f"{AGENT_NAME} v{__version__} ({__release_date__}) - Self-Hosted Personal AI System"
    line1 = line1[:w - 2].center(w - 2)
    out.append(f"{BOLD}{_fg(SKIN['banner_border'])}║{RST} {_fg(SKIN['banner_title'])}{line1}{RST} {BOLD}{_fg(SKIN['banner_border'])}║{RST}")
    # Hippo art + tools/skills (Hermes layout: art kiri, info kanan)
    try:
        h = _get("/health", timeout=3)
        n_tools = h.get("tools", 0)
        n_skills = h.get("skills", 0)
    except Exception:
        n_tools, n_skills = 0, 0
    try:
        g = _get("/v1/agents/goals?status=active", timeout=3)
        n_goals = (g.get("stats") or {}).get("active", 0)
    except Exception:
        n_goals = 0
    info_lines = [
        f"{_fg(SKIN['banner_text'])}Tools: {n_tools}  Skills: {n_skills}  Niat: {n_goals}{RST}",
        f"{_fg(SKIN['banner_dim'])}/help untuk commands · /matter <teks> untuk niat{RST}",
    ]
    n_art = len(HIPPO_ART)
    for i, art in enumerate(HIPPO_ART):
        if i < len(info_lines):
            info = info_lines[i]
        elif i == len(info_lines):
            info = f"{_fg(SKIN['banner_accent'])}{API.replace('http://', '')}{RST}"
        else:
            info = ""
        out.append(f"{BOLD}{_fg(SKIN['banner_border'])}║{RST} {_fg(SKIN['banner_text'])}{art}{RST}  {info}")
    out.append(f"{BOLD}{_fg(SKIN['banner_border'])}╚{bar}╝{RST}")
    return "\n".join(out)


def banner() -> None:
    print(build_banner())


# ── Status bar (Hermes _build_status_bar_text — compact one-line) ──

def build_status_bar(session_start: "datetime | None" = None, goal_text: str = "") -> str:
    try:
        h = _get("/health", timeout=3)
        status = h.get("status", "?")
        icon = {"healthy": "●", "degraded": "◐", "down": "○"}.get(status, "○")
        parts = [f"{_fg(SKIN['status_bar_good'])}{icon} api{RST}"]
    except Exception:
        parts = [f"{_fg(SKIN['status_bar_bad'])}○ api{RST}"]
    if session_start:
        el = max(0, int((datetime.now() - session_start).total_seconds()))
        dur = f"{el // 3600}h{el % 3600 // 60:02d}m" if el >= 3600 else f"{el // 60}m{el % 60:02d}s"
        parts.append(f"{_fg(SKIN['status_bar_text'])}⏱ {dur}{RST}")
    if goal_text:
        gt = goal_text[:30] + ("…" if len(goal_text) > 30 else "")
        parts.append(f"{_fg(SKIN['status_bar_strong'])}🎯 {gt}{RST}")
    try:
        sch = _get("/scheduler/health", timeout=3)
        if sch.get("running"):
            parts.append(f"{_fg(SKIN['status_bar_dim'])}⚙ scheduler{RST}")
    except Exception:
        pass
    return " │ ".join(parts)
# ════════════════════════════════════════════════════════════════
# v63 BAGIAN 2: command handlers + REPL + TUI (prompt_toolkit)
# ════════════════════════════════════════════════════════════════

import argparse
from datetime import datetime

# ── Session state (REPL) ──
_state = {
    "session_id": f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "user_id": "sen",
    "session_start": datetime.now(),
    "timestamps": False,
    "verbose": False,
    "history": [],          # [(role, text)]
    "last_user_input": "",
}


def _now_tag() -> str:
    if not _state["timestamps"]:
        return ""
    return f"{DIM}[{datetime.now().strftime('%H:%M')}] {RST}"


def _record(role: str, text: str) -> None:
    _state["history"].append((role, text))
    if len(_state["history"]) > 200:
        _state["history"] = _state["history"][-200:]


def _err(text: str) -> None:
    print(f"  {_fg(SKIN['ui_error'])}✗ {text}{RST}")


def _ok(text: str) -> None:
    print(f"  {_fg(SKIN['ui_ok'])}✓ {text}{RST}")


def _dim(text: str) -> None:
    print(f"  {DIM}{text}{RST}")


# ════════════════ Session commands ════════════════

def cmd_new(args):
    _state["session_id"] = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    _state["session_start"] = datetime.now()
    _state["history"].clear()
    _ok(f"sesi baru: {_state['session_id']}")


def cmd_history(args):
    n = int(args[0]) if args else 20
    try:
        r = _get(f"/v1/memory/session/history?session_id={_state['session_id']}&user_id={_state['user_id']}")
        msgs = r.get("history", [])
        if not msgs:
            _dim("belum ada history di sesi ini")
            return
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}History ({len(msgs[-n:])} terakhir){RST}")
        for m in msgs[-n:]:
            role = "❯" if m.get("role") == "user" else "⚕"
            color = SKIN["prompt"] if m.get("role") == "user" else SKIN["status_bar_strong"]
            print(f"  {_now_tag()}{_fg(color)}{role}{RST} {str(m.get('content', ''))[:200]}")
        print()
    except Exception as e:
        _err(f"history gagal: {e}")


def cmd_save(args):
    try:
        r = _post("/v1/tasks/submit", {"task": "handoff sesi CLI",
                                        "context": json.dumps(_state["history"][-20:])})
        _ok(f"handoff tersimpan (task: {r.get('task_id', r)})")
    except Exception as e:
        # fallback: simpan lokal
        path = os.path.expanduser(f"~/aeryn-core-agent/data/handoff-{_state['session_id']}.json")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump({"session": _state["session_id"],
                           "history": _state["history"][-20:]}, f, ensure_ascii=False)
            _ok(f"handoff lokal: {path}")
        except Exception as e2:
            _err(f"save gagal: {e} / {e2}")


def cmd_retry(args):
    if not _state["last_user_input"]:
        _dim("belum ada pesan untuk diulang")
        return
    _do_chat(_state["last_user_input"])


def cmd_goals_cmd(args):
    try:
        r = _get("/v1/agents/goals?status=active")
        goals = [g for g in r.get("goals", []) if g.get("status") != "completed"]
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}🎯 Niat Aktif ({len(goals)}){RST}")
        if not goals:
            _dim("belum ada niat — /matter <teks> untuk mulai")
        for g in goals[:10]:
            prog = int(g.get("progress", 0))
            bar = "█" * (prog // 10) + "░" * (10 - prog // 10)
            print(f"  {_fg(SKIN['banner_accent'])}{g.get('title', '?')[:40]:42s}{RST} "
                  f"{bar} {prog}%")
        print()
    except Exception as e:
        _err(f"goals gagal: {e}")


def cmd_goal_detail(args):
    if not args:
        _dim("pakai: /goal <id>")
        return
    try:
        gid = args[0]
        r = _get(f"/v1/agents/goals/{gid}/progress")
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1000])
    except Exception as e:
        _err(f"goal gagal: {e}")


def cmd_steer(args):
    if len(args) < 2:
        _dim("pakai: /steer <id> <pesan arahan>")
        return
    gid, msg = args[0], " ".join(args[1:])
    try:
        r = _post("/v1/agents/goals/pursue", {"goal_id": gid, "steer": msg})
        _ok(f"steer terkirim: {str(r)[:120]}")
    except Exception as e:
        _err(f"steer gagal: {e}")


def cmd_status_cmd(args):
    try:
        obs = _get("/v1/obs/summary?window_hours=24")
        g = _get("/v1/agents/goals?status=active")
        st = g.get("stats") or {}
        reqs = obs.get("requests") or {}
        h = _get("/health")
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}● {h.get('status')}{RST} {DIM}· v{__version__} · {h.get('memory_mb', 0)} MB{RST}")
        print(f"  24h: {reqs.get('total', 0)} req · err {reqs.get('error_rate', 0)}% · "
              f"goals {st.get('active', 0)} aktif / {st.get('completed', 0)} selesai")
        subs = obs.get("subsystems") or {}
        line = "  ".join(f"{_fg(SKIN['ui_ok'])}{k}{RST}" if (v or {}).get("status") == "healthy"
                         else f"{_fg(SKIN['ui_warn'])}{k}{RST}" for k, v in subs.items())
        print(f"  subsistem: {line}\n")
    except Exception as e:
        _err(f"status gagal: {e}")


def cmd_tasks(args):
    try:
        r = _get("/v1/tasks/")
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1200])
    except Exception as e:
        _err(f"tasks gagal: {e}")


def cmd_workflows_cmd(args):
    try:
        r = _get("/workflows")
        print(json.dumps(r, indent=2, ensure_ascii=False)[:1200])
    except Exception as e:
        _err(f"workflows gagal: {e}")


def cmd_traces_cmd(args):
    n = args[0] if args else "10"
    try:
        r = _get(f"/observability/traces?limit={n}")
        for t in (r.get("traces") or [])[:int(n)]:
            print(f"  {_fg(SKIN['status_bar_dim'])}{t.get('id', '?')[:12]}{RST} "
                  f"· {t.get('session_id', '?')[:30]} · {t.get('spans', '?')} spans")
    except Exception as e:
        _err(f"traces gagal: {e}")


def cmd_matter_cmd(args):
    text = " ".join(args)
    if not text:
        _dim("pakai: /matter <teks>")
        return
    try:
        r = _post("/matter", {"text": text})
        if r.get("ok"):
            _ok(f"tercatat: {r.get('message', text)[:100]}")
        else:
            _err(f"matter gagal: {r.get('error', '?')}")
    except Exception as e:
        _err(f"matter gagal: {e}")


# ════════════════ Configuration commands ════════════════

def cmd_config(args):
    try:
        r = _get("/gateway/env")
        print(json.dumps(r, indent=2, ensure_ascii=False)[:900])
    except Exception as e:
        _err(f"config gagal: {e}")


def cmd_model(args):
    _dim(f"model CLI mengikuti config Aeryn (LM router). Lihat /gateway/env atau config API.")


def cmd_approvals(args):
    try:
        r = _get("/v1/approvals/pending")
        pending = r.get("pending", [])
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}Approval Queue ({len(pending)}){RST}")
        if not pending:
            _dim("kosong — semua approved")
        for p in pending[:10]:
            print(f"  {_fg(SKIN['ui_warn'])}[{p.get('risk_level')}] {p.get('tool_name')}{RST} "
                  f"{DIM}id={p.get('id', '?')[:12]}{RST}")
        print()
    except Exception as e:
        _err(f"approvals gagal: {e}")


def cmd_timestamps(args):
    val = (args[0].lower() if args else "").strip()
    _state["timestamps"] = val != "off"
    _ok(f"timestamps {'ON' if _state['timestamps'] else 'OFF'}")


def cmd_verbose(args):
    val = (args[0].lower() if args else "").strip()
    _state["verbose"] = val != "off"
    _ok(f"verbose {'ON' if _state['verbose'] else 'OFF'}")


def cmd_scheduler_cmd(args):
    try:
        r = _get("/scheduler/health")
        icon = "●" if r.get("running") else "○"
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}{icon} Scheduler (Rust native){RST}")
        print(f"  running   : {r.get('running')}")
        print(f"  tick_count: {r.get('tick_count')}")
        print(f"  tick_ms   : {r.get('tick_interval_ms', r.get('tick_interval', '?'))}")
        print(f"  last_daily: {r.get('last_daily_ago_s', '?')}s ago")
        errs = r.get("errors") or []
        if errs:
            for e in errs[:3]:
                _err(str(e)[:80])
        print()
    except Exception as e:
        _err(f"scheduler gagal: {e}")


def cmd_sensor_cmd(args):
    sub = args[0] if args else "weather"
    try:
        r = _get(f"/sensor/{sub}")
        if sub == "weather":
            print(f"\n  {_fg(SKIN['ui_accent'])}🌤️  {r.get('temperature_c', '?')}°C · {r.get('condition', '')}{RST}\n")
        elif sub == "calendar":
            items = r.get("items") or r.get("upcoming") or []
            print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}📅 Agenda ({r.get('count', len(items))}){RST}")
            for it in items[:10]:
                print(f"  {it.get('when', it.get('time', '?')):22s} {str(it.get('what', it.get('text', '?')))[:50]}")
            print()
        else:
            print(json.dumps(r, indent=2, ensure_ascii=False)[:600])
    except Exception as e:
        _err(f"sensor gagal: {e}")


def cmd_cost_cmd(args):
    try:
        r = _get("/cost")
        est = (r.get("spend") or {}).get("estimate_usd", 0)
        print(f"\n  {_fg(SKIN['ui_accent'])}💰 Cost estimate: ${est:.4f}{RST}\n")
    except Exception as e:
        _err(f"cost gagal: {e}")


# ════════════════ Info commands ════════════════

def cmd_whoami(args):
    try:
        r = _get("/.well-known/agent.json")
        print(f"\n  {BOLD}{_fg(SKIN['banner_title'])}⚕ {r.get('name')}{RST} {DIM}(A2A proto {r.get('protocolVersion')}){RST}")
        print(f"  {r.get('description', '')[:300]}\n")
    except Exception as e:
        _err(f"whoami gagal: {e}")


def cmd_profile(args):
    el = int((datetime.now() - _state["session_start"]).total_seconds())
    print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}Profile{RST}")
    print(f"  user       : {_state['user_id']}")
    print(f"  session    : {_state['session_id']}")
    print(f"  durasi     : {el // 60}m{el % 60:02d}s")
    print(f"  messages   : {len(_state['history'])}")
    print(f"  timestamps : {'on' if _state['timestamps'] else 'off'} · verbose: {'on' if _state['verbose'] else 'off'}\n")


def cmd_help(args):
    query = " ".join(args).lower().strip()
    w = 55
    print(f"\n{BOLD}+{'-' * w}+{RST}")
    print(f"{BOLD}|{'(^_^)? Available Commands':^{w}}|{RST}")
    print(f"{BOLD}+{'-' * w}+{RST}")
    for category, cmds in COMMANDS_BY_CATEGORY.items():
        shown = []
        for c in cmds:
            if query and query not in c[0].lower() and query not in c[1].lower():
                continue
            shown.append(c)
        if not shown:
            continue
        print(f"\n  {BOLD}{_fg(SKIN['ui_label'])}{category}{RST}")
        for name, desc, hint, _fn in shown:
            label = f"{name} {hint}".strip()
            print(_fmt_label(f"{label:<22}", desc))
    print()
    _dim(f"pesan biasa → chat · {PROMPT_SYMBOL} prompt · /quit keluar")


def cmd_version(args):
    _ok(f"Aeryn CLI v{__version__} ({__release_date__}) — Self-Hosted Personal AI System")


def cmd_env_cmd(args):
    try:
        r = _get("/gateway/env")
        env = r.get("environment") or {}
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}🌍 Environment{RST}")
        print(f"  type : {env.get('type', '?')}")
        print(f"  db   : {env.get('db', '?')}")
        print(f"  api  : {API}\n")
    except Exception as e:
        _err(f"env gagal: {e}")


def cmd_services_cmd(args):
    import subprocess
    try:
        r = subprocess.run(["sh", "-c", "ls $PREFIX/var/service 2>/dev/null"],
                           capture_output=True, timeout=5)
        svcs = (r.stdout.decode() or "").split()
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}Services runit ({len(svcs)}){RST}")
        for s in sorted(svcs):
            try:
                st = subprocess.run(["sh", "-c", f"sv status $PREFIX/var/service/{s} 2>/dev/null | head -1"],
                                    capture_output=True, timeout=3)
                line = st.stdout.decode().strip()
            except Exception:
                line = "?"
            icon = _fg(SKIN['ui_ok']) + "●" if "run" in line else _fg(SKIN['ui_error']) + "○"
            print(f"  {icon}{RST} {s:28s} {DIM}{line[:40]}{RST}")
        print()
    except Exception as e:
        _err(f"services gagal: {e}")


def cmd_briefing_cmd(args):
    try:
        r = _get("/briefing/preview")
        print(f"\n  {BOLD}{_fg(SKIN['banner_accent'])}🌅 Briefing{RST}")
        print("  " + str(r.get("briefing", r))[:1500].replace("\n", "\n  "))
        print()
    except Exception as e:
        _err(f"briefing gagal: {e}")


# ════════════════ Tools & Skills commands ════════════════

def cmd_tools_cmd(args):
    try:
        r = _get("/tools")
        tools = r.get("tools", [])
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}🔧 Tools ({r.get('count', len(tools))}){RST}")
        for t in tools[:25]:
            print(f"  {_fg(SKIN['banner_accent'])}{t.get('name', '?'):24s}{RST} {DIM}{str(t.get('description', ''))[:60]}{RST}")
        print()
    except Exception as e:
        _err(f"tools gagal: {e}")


def cmd_skills_cmd(args):
    try:
        r = _get("/skills")
        skills = r.get("skills", [])
        print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}⚡ Skills ({r.get('count', len(skills))}){RST}")
        for s in skills[:25]:
            print(f"  {_fg(SKIN['banner_accent'])}{s.get('name', '?'):30s}{RST} {DIM}{str(s.get('description', ''))[:55]}{RST}")
        print()
    except Exception as e:
        _err(f"skills gagal: {e}")


def cmd_memory_cmd(args):
    query = " ".join(args)
    if not query:
        _dim("pakai: /memory <query>")
        return
    try:
        from aeryn_core.platform.internal_tools import tool_memory_search
        r = tool_memory_search(query, limit=5)
        if r.get("ok"):
            out = r.get("output", "")
            print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}🔍 '{query}'{RST}\n")
            print("  " + out[:1500].replace("\n", "\n  "))
            print()
        else:
            _err(f"search: {r.get('error', 'no results')}")
    except Exception as e:
        # fallback via API hybrid search
        try:
            r = _get(f"/v1/memory/hybrid/search?q={_urlquote(query)}")
            print(json.dumps(r, indent=2, ensure_ascii=False)[:900])
        except Exception as e2:
            _err(f"memory gagal: {e} / {e2}")


def cmd_horizon_cmd(args):
    if not args:
        _dim("pakai: /horizon plan <goal> | status <id> | execute <id>")
        return
    sub = args[0]
    rest = args[1:]
    try:
        if sub == "plan":
            goal = " ".join(rest)
            if not goal:
                _dim("pakai: /horizon plan <goal>")
                return
            r = _post("/horizon/plan", {"goal": goal})
            _ok(f"task {r.get('task_id')} · {r.get('steps', 0)} langkah")
        elif sub == "status":
            r = _get(f"/horizon/status/{rest[0]}")
            print(json.dumps(r, indent=2, ensure_ascii=False)[:900])
        elif sub == "execute":
            r = _post(f"/horizon/execute/{rest[0]}?max_steps=1", {})
            print(json.dumps(r, indent=2, ensure_ascii=False)[:900])
        else:
            _dim(f"unknown sub: {sub}")
    except Exception as e:
        _err(f"horizon gagal: {e}")


def cmd_learning_cmd(args):
    sub = args[0] if args else "status"
    try:
        if sub == "consolidate":
            r = _post("/learning/consolidate", {})
            _ok(f"patterns={r.get('patterns', 0)} · crystallized={len(r.get('crystallized', []))}")
        else:
            r = _get("/learning/status")
            pats = r.get("patterns", [])
            print(f"\n  {BOLD}{_fg(SKIN['ui_accent'])}🧠 Patterns ({r.get('count', len(pats))}){RST}")
            for p in pats[:10]:
                print(f"  {_fg(SKIN['banner_accent'])}{p.get('signature', '?')[:40]}{RST} "
                      f"{DIM}×{p.get('frequency', '?')}{RST}")
            print()
    except Exception as e:
        _err(f"learning gagal: {e}")


def cmd_quit(args):
    raise SystemExit(0)


# ════════════════ Chat (agent loop penuh) ════════════════

def _do_chat(message: str) -> None:
    _state["last_user_input"] = message
    _record("user", message)
    try:
        r = _post("/v1/chat", {"message": message,
                              "session_id": _state["session_id"],
                              "user_id": _state["user_id"]}, timeout=180)
        out = r.get("content") or r.get("response") or ""
        if not out:
            _err("respons kosong (LM gagal?)")
            return
        _record("assistant", out)
        # Response border Hermes-style (gold ═)
        print(f"  {_fg(SKIN['input_rule'])}─" * 3 + f"{RST} {_fg(SKIN['response_border'])}⚕ Aeryn{RST}")
        print("  " + out.replace("\n", "\n  "))
        if _state["verbose"]:
            tool = r.get("tool_used") or r.get("tool")
            if tool:
                _dim(f"tool: {tool}")
    except Exception as e:
        # fallback /chat (goals)
        try:
            r = _post("/chat", {"goal": message, "session_id": _state["session_id"]})
            out = r.get("response") or ""
            if out:
                _record("assistant", out)
                print(f"  {_fg(SKIN['response_border'])}⚕ Aeryn{RST} {out[:800]}")
            else:
                _err(f"chat gagal: {e}")
        except Exception as e2:
            _err(f"chat gagal: {e} / {e2}")


# ════════════════ Dispatch ════════════════

def dispatch(line: str) -> None:
    line = line.strip()
    if not line:
        return
    if line.startswith("/"):
        parts = line[1:].split()
        name = "/" + (parts[0].lower() if parts else "")
        args = parts[1:]
        if name in ALL_COMMANDS:
            handler = globals()[ALL_COMMANDS[name][3]]
            handler(args)
        else:
            _dim(f"unknown {name} — /help untuk daftar")
    else:
        _do_chat(line)


# ════════════════ REPL (non-TUI fallback — input() sederhana) ════════════════

def run_repl() -> int:
    banner()
    print(f"  {DIM}{WELCOME}{RST}")
    print(f"  {build_status_bar(_state['session_start'])}\n")
    while True:
        try:
            line = input(f"{_fg(SKIN['prompt'])}{PROMPT_SYMBOL}{RST} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {DIM}sampai jumpa~{RST}")
            return 0
        if not line:
            continue
        if line in ("/quit", "/exit"):
            print(f"\n  {DIM}sampai jumpa~{RST}")
            return 0
        dispatch(line)
        print()


# ════════════════ TUI (prompt_toolkit — fixed input area, seperti Hermes) ════════════════

def run_tui() -> int:
    """TUI ala Hermes: prompt_toolkit dengan patch_stdout + status bar bawah
    + slash completion. Input tetap fokus (tidak hilang oleh refresh)."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import Completer, Completion
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.patch_stdout import patch_stdout
        from prompt_toolkit.shortcuts import print_formatted_text
    except ImportError:
        print(f"{DIM}prompt_toolkit tidak ada — REPL mode{RST}")
        return run_repl()

    class SlashCompleter(Completer):
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            if text.startswith("/") and " " not in text:
                for name in sorted(ALL_COMMANDS.keys()):
                    if name.startswith(text):
                        cat, desc, hint, _fn = ALL_COMMANDS[name]
                        yield Completion(name, start_position=-len(text),
                                         display=f"{name} {hint}".strip(),
                                         display_meta=desc[:40])

    banner()
    print(f"  {DIM}{WELCOME}{RST}")
    print(f"  {build_status_bar(_state['session_start'])}\n")

    history = InMemoryHistory()
    session = PromptSession(history=history, completer=SlashCompleter(),
                            complete_while_typing=True)

    try:
        with patch_stdout(raw=True):
            while True:
                try:
                    line = session.prompt(
                        f"{_fg(SKIN['prompt'])}{PROMPT_SYMBOL} {RST}").strip()
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
                if not line:
                    continue
                if line in ("/quit", "/exit"):
                    break
                dispatch(line)
                # status bar bawah (Hermes-style: setelah tiap turn)
                print_formatted_text(f"{DIM}{build_status_bar(_state['session_start'])}{RST}")
    except KeyboardInterrupt:
        pass
    print(f"\n  {DIM}sampai jumpa~{RST}")
    return 0


# ════════════════ main() ════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aeryn",
        description=f"Aeryn v{__version__} — Self-Hosted Personal AI System (CLI/TUI ala Hermes)")
    parser.add_argument("command", nargs="?", default="tui",
                        help="tui|repl|status|goals|chat <pesan>|matter <teks>|help")
    parser.add_argument("rest", nargs="*", help="argumen command")
    parser.add_argument("--api", default=API,
                        help="URL API Aeryn")
    args = parser.parse_args()

    _set_api(args.api)

    cmd = args.command
    rest = args.rest
    if cmd == "tui":
        return run_tui()
    if cmd == "repl":
        return run_repl()
    if cmd == "help":
        banner()
        cmd_help(rest)
        return 0
    if cmd == "chat":
        if not rest:
            print("pakai: aeryn chat <pesan>")
            return 1
        banner()
        _do_chat(" ".join(rest))
        return 0
    if cmd == "status":
        banner()
        cmd_status_cmd(rest)
        return 0
    if cmd == "goals":
        banner()
        cmd_goals_cmd(rest)
        return 0
    if cmd == "matter":
        banner()
        cmd_matter_cmd(rest)
        return 0 if not rest else 0
    # default: jalankan sebagai command REPL satu kali
    banner()
    dispatch(f"/{cmd} " + " ".join(rest) if cmd in [c[0][1:] for c in COMMANDS_BY_CATEGORY.values() for c in c] else cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
