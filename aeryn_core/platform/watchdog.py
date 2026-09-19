#!/usr/bin/env python3
"""V61.4 — IN2+IN3: Aeryn Watchdog — self-reporting monitoring.

Monitor kesehatan service (aeryn-api, postgres, redis) tiap interval.
Mati/restart berulang → ALERT ke Sen via termux-notification + catat ke
bitemporal facts (riwayat kejadian jadi bagian memori Aeryn).
Real API only — no test doubles.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Optional

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
API_URL = os.environ.get("AERYN_WATCHDOG_API_URL", "http://127.0.0.1:3010/health")
PG_URL = os.environ.get("AERYN_WATCHDOG_PG_URL", "postgresql://sen@127.0.0.1:5432/aeryn")
REDIS_HOST = os.environ.get("AERYN_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("AERYN_REDIS_PORT", "6379"))
INTERVAL = int(os.environ.get("AERYN_WATCHDOG_INTERVAL", "60"))
ALERT_THRESHOLD = int(os.environ.get("AERYN_WATCHDOG_THRESHOLD", "2"))
LOG_FILE = os.environ.get("AERYN_WATCHDOG_LOG", os.path.join(HOME, "tmp", "aeryn-watchdog.log"))

# Bitemporal facts store (IN3)
sys.path.insert(0, os.path.join(REPO, "aeryn_core", "memory"))
try:
    from aeryn_core.memory.fact_store import get_fact_store
except Exception:
    get_fact_store = None


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_api() -> bool:
    """aeryn-api health endpoint reachable?"""
    try:
        out = subprocess.run(
            ["curl", "-s", "-m", "5", API_URL],
            capture_output=True, text=True, timeout=8,
        )
        return out.returncode == 0 and "healthy" in (out.stdout or "")
    except Exception:
        return False


def check_pg() -> bool:
    """Postgres accepting queries?"""
    try:
        out = subprocess.run(
            ["psql", PG_URL, "-c", "SELECT 1"],
            capture_output=True, text=True, timeout=8,
        )
        return out.returncode == 0
    except Exception:
        return False


def check_redis() -> bool:
    """Redis PING?"""
    try:
        out = subprocess.run(
            ["redis-cli", "-h", REDIS_HOST, "-p", str(REDIS_PORT), "ping"],
            capture_output=True, text=True, timeout=5,
        )
        return out.returncode == 0 and "PONG" in (out.stdout or "")
    except Exception:
        return False


def notify(title: str, body: str) -> bool:
    """Alert ke Sen via termux-notification. Real API — no stub."""
    try:
        out = subprocess.run(
            ["termux-notification", "--title", title, "--content", body,
             "--priority", "high"],
            capture_output=True, text=True, timeout=10,
        )
        return out.returncode == 0
        # termux-notification needs Termux:API app + notification permission;
        # returncode 0 saat delivery OK.
    except FileNotFoundError:
        return False
    except Exception:
        return False


def record_fact(entity: str, predicate: str, fact: str) -> None:
    """Catat kejadian ke bitemporal facts (IN3) — riwayat jadi memori Aeryn."""
    if get_fact_store is None:
        return
    try:
        fs = get_fact_store()
        fs.record(
            entity=entity,
            predicate=predicate,
            fact=fact,
            source="watchdog",
            confidence=1.0,
        )
    except Exception as e:
        # Watchdog tidak boleh mati karena gagal catat — log saja
        print(f"[{_now()}] fact-record failed: {e}", flush=True)


def _log(msg: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


def run_checks() -> dict:
    """Run all service checks, return structured status."""
    return {
        "api": check_api(),
        "pg": check_pg(),
        "redis": check_redis(),
        "checked_at": _now(),
    }


# ── Fail-counter state (tahan restart via file) ────────────────────────

def _state_path() -> str:
    return os.environ.get(
        "AERYN_WATCHDOG_STATE", os.path.join(HOME, "tmp", "aeryn-watchdog-state.json")
    )


def _load_state() -> dict:
    try:
        with open(_state_path()) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(_state_path()), exist_ok=True)
    with open(_state_path(), "w") as f:
        json.dump(state, f, indent=2)


def _alert_if_needed(service: str, fails: int, ok: bool) -> None:
    """Alert sekali saat melewati threshold; reset saat recovered."""
    state = _load_state()
    key = f"fails.{service}"
    prev = state.get("alerts", {})

    if not ok and fails >= ALERT_THRESHOLD:
        if not prev.get(service):
            _log(f"ALERT: {service} DOWN ({fails}x beruntun)")
            notify(
                f"⚠️ Aeryn: {service} DOWN",
                f"{service} gagal {fails}x beruntun pada {_now()}. "
                f"Cek: sv status {service} / redis-cli ping / curl {API_URL}",
            )
            record_fact(
                service, "status", f"DOWN {fails}x beruntun pada {_now()}"
            )
            state.setdefault("alerts", {})[service] = True
    else:
        if ok and prev.get(service):
            _log(f"RECOVERED: {service} UP kembali pada {_now()}")
            notify(f"✅ Aeryn: {service} UP", f"{service} recovered pada {_now()}")
            record_fact(service, "status", f"RECOVERED pada {_now()}")
            state.setdefault("alerts", {}).pop(service, None)
    state.setdefault("fails", {})[service] = 0 if ok else fails
    _save_state(state)


def tick() -> dict:
    """One watchdog tick: run checks + alert + record. Returns status dict."""
    status = run_checks()
    fails_state = _load_state().get("fails", {})
    for svc, ok in (
        ("aeryn-api", status["api"]),
        ("postgres", status["pg"]),
        ("redis", status["redis"]),
    ):
        fails = int(fails_state.get(svc, 0)) + (0 if ok else 1)
        _alert_if_needed(svc, fails, ok)
    return status


def loop() -> None:
    """Watchdog main loop (untuk daemon runit service)."""
    print(f"[{_now()}] Aeryn watchdog started (interval {INTERVAL}s)", flush=True)
    while True:
        try:
            status = tick()
            _log(
                f"tick: api={status['api']} pg={status['pg']} "
                f"redis={status['redis']}"
            )
        except Exception as e:
            _log(f"tick error: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    loop()
