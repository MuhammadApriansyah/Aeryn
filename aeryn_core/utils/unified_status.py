#!/usr/bin/env python3
"""V62.7 — T2.1: Unified status module — SATU sumber kebenaran untuk semua permukaan.

Dipakai oleh: CLI (aeryn status/tools/search/env), TUI, API (/health, /v1/tools,
/v1/skills). Env detection, tools count, skills count, version — semuanya dari
sini. Real APIs only — no test doubles.
"""

import os
import sys
import json
import subprocess
from datetime import datetime

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
API_URL = os.environ.get("AERYN_API_URL", "http://127.0.0.1:3010")


def get_version() -> str:
    """Version dari SATU tempat: pyproject.toml (fallback hardcode)."""
    pyproject = os.path.join(REPO, "pyproject.toml")
    try:
        with open(pyproject) as f:
            for line in f:
                if line.strip().startswith("version"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return "62.1"


def detect_environment() -> dict:
    """Deteksi environment NYATA (native Termux / proot-distro / host)."""
    is_termux = "com.termux" in (os.environ.get("PREFIX", "") or "")
    # Cek proot-distro login (env var TERMUX proot-distro sets)
    login_html = "/proc/self/loginuid"
    kind = "host"
    if is_termux:
        kind = "termux-native"
        # proot-distro menandai via PRELOAD/PATH khusus — cek indicator
        if os.path.exists("/.proot-distro") or "proot-distro" in (os.environ.get("PATH", "")):
            kind = "proot-distro"
    # DB backend NYATA — cek env var, lalu .env repo, lalu DEFAULT dari aeryn-api service
    db_backend = "sqlite"
    pg_url = os.environ.get("NEON_DATABASE_URL", "")
    if not pg_url:
        # CLI/TUI sering jalan tanpa env — baca .env repo (sumber config service)
        env_file = os.path.join(REPO, ".env")
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NEON_DATABASE_URL="):
                        pg_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
                    if line.startswith("AERYN_DB=") and "postgres" in line:
                        db_backend = "postgres"
                        break
        except OSError:
            pass
    if pg_url.startswith("postgresql"):
        db_backend = "postgres"
    return {"type": kind, "db": db_backend}


def get_tools_count() -> int:
    """Jumlah tools ter-register (dari plugin_registry — sumber yang sama dgn chat)."""
    try:
        from aeryn_core.platform.plugin_registry import get_registry
        return len(get_registry().list_tools())
    except Exception:
        return 0


def get_skills_count() -> int:
    """Jumlah skills aktif (dari crystallized DB — sumber yang sama dgn /v1/skills)."""
    try:
        from aeryn_core.utils.config import DATABASE_DIR
        import sqlite3
        db = os.path.join(DATABASE_DIR, "skill_crystallization.db")
        if not os.path.exists(db):
            return 0
        conn = sqlite3.connect(db)
        n = conn.execute("SELECT COUNT(*) FROM crystallized_skills WHERE is_active=1").fetchone()[0]
        conn.close()
        return int(n)
    except Exception:
        return 0


def get_services() -> list:
    """Status service runit (aeryn-api, worker, watchdog, redis, postgres)."""
    services = []
    checks = [
        ("aeryn-api", ["curl", "-s", "-m", "3", f"{API_URL}/health"]),
        ("redis", ["redis-cli", "ping"]),
        ("postgres", ["psql",
                      os.environ.get("NEON_DATABASE_URL", "postgresql://sen@127.0.0.1:5432/aeryn"),
                      "-c", "SELECT 1"]),
    ]
    for name, cmd in checks:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            ok = out.returncode == 0
            if name == "aeryn-api":
                ok = ok and "healthy" in (out.stdout or "")
            elif name == "redis":
                ok = ok and "PONG" in (out.stdout or "")
            services.append({"name": name, "status": "up" if ok else "down"})
        except Exception:
            services.append({"name": name, "status": "down"})
    # worker + watchdog via runit supervise pid
    for name in ("aeryn-worker", "aeryn-watchdog"):
        pid_file = os.path.join(
            os.environ.get("PREFIX", "/data/data/com.termux/files/usr"),
            "var", "service", name, "supervise", "pid",
        )
        try:
            pid = int(open(pid_file).read().strip())
            os.kill(pid, 0)  # signal 0 = alive check
            services.append({"name": name, "status": "up"})
        except Exception:
            services.append({"name": name, "status": "down"})
    return services


def get_full_status() -> dict:
    """Full status object — SATU sumber untuk semua permukaan."""
    api_health = "unknown"
    try:
        out = subprocess.run(["curl", "-s", "-m", "3", f"{API_URL}/health"],
                             capture_output=True, text=True, timeout=6)
        if out.returncode == 0 and out.stdout.strip():
            try:
                api_health = json.loads(out.stdout).get("status", "unknown")
            except json.JSONDecodeError:
                api_health = "unknown"
    except Exception:
        pass
    env = detect_environment()
    services = get_services()
    overall = "healthy" if all(s["status"] == "up" for s in services) else (
        "degraded" if any(s["status"] == "up" for s in services) else "down"
    )
    return {
        "status": overall,
        "api": api_health,
        "version": get_version(),
        "env": env,
        "tools": get_tools_count(),
        "skills": get_skills_count(),
        "services": services,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def format_cli(status: dict) -> str:
    """Format status untuk CLI/TUI display."""
    icon = {"healthy": "●", "degraded": "◐", "down": "○"}.get(status["status"], "○")
    lines = [
        "",
        f"  📊 Aeryn Status",
        "",
        f"  Status:   {icon} {status['status']}",
        f"  Version:  v{status['version']}",
        f"  Env:      {status['env']['type']} · DB: {status['env']['db']}",
        f"  Tools:    🔧 {status['tools']} ter-register",
        f"  Skills:   ⚡ {status['skills']} aktif",
        "",
        f"  Services:",
    ]
    for s in status["services"]:
        s_icon = "●" if s["status"] == "up" else "○"
        lines.append(f"    {s_icon} {s['name']}: {s['status']}")
    lines.append("")
    lines.append(f"  Checked:  {status['checked_at']}")
    return "\n".join(lines)
