#!/usr/bin/env python3
"""V61.4 — IN1: Redis job-queue untuk daemon Aeryn (goal-pursuit & task antre).

Tahan restart: job di redis (bukan in-memory), auto-start via runit service.
Wire: daemon pake push/pop/length/ping via redis-py (8.1.0).
Real API only — no test doubles.
"""

import os
import json
import time
from typing import Optional, List

try:
    import redis as _redis_mod
except ImportError:
    _redis_mod = None

REDIS_HOST = os.environ.get("AERYN_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("AERYN_REDIS_PORT", "6379"))
QUEUE_KEY = os.environ.get("AERYN_QUEUE_KEY", "aeryn:jobs")
DLQ_KEY = os.environ.get("AERYN_DLQ_KEY", "aeryn:jobs:dlq")

_conn = None


def connect():
    """Get (and cache) a redis connection. Raises if redis unavailable."""
    global _conn
    if _conn is None:
        if _redis_mod is None:
            raise RuntimeError("redis-py tidak ter-install (pip install redis)")
        _conn = _redis_mod.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True,
            socket_connect_timeout=2, socket_timeout=2,
        )
        _conn.ping()
    return _conn


def ping() -> bool:
    """Health check: redis reachable?"""
    try:
        return bool(connect().ping())
    except Exception:
        return False


def push(job: dict) -> str:
    """Enqueue a job (LPUSH for FIFO via BRPOP). Returns job id."""
    r = connect()
    job_id = job.get("id") or f"job_{int(time.time() * 1000)}"
    job = {**job, "id": job_id, "queued_at": time.time()}
    r.lpush(QUEUE_KEY, json.dumps(job))
    return job_id


def pop(timeout: int = 5) -> Optional[dict]:
    """Dequeue a job (blocking BRPOP). None on timeout/empty."""
    r = connect()
    item = r.brpop(QUEUE_KEY, timeout=timeout)
    if not item:
        return None
    try:
        return json.loads(item[1])
    except (json.JSONDecodeError, TypeError):
        r.lpush(DLQ_KEY, item[1])
        return None


def length() -> int:
    """Queue depth."""
    try:
        return int(connect().llen(QUEUE_KEY))
    except Exception:
        return 0


def dlq_length() -> int:
    """Dead-letter queue depth."""
    try:
        return int(connect().llen(DLQ_KEY))
    except Exception:
        return 0


def ack(job_id: str) -> bool:
    """Mark job done (processing list cleanup)."""
    try:
        connect().lrem("aeryn:jobs:processing", 0, job_id)
        return True
    except Exception:
        return False


def stats() -> dict:
    """Queue stats untuk monitoring."""
    r = connect()
    return {
        "redis": ping(),
        "jobs": r.llen(QUEUE_KEY),
        "processing": r.llen("aeryn:jobs:processing"),
        "dlq": r.llen(DLQ_KEY),
    }


# ── Worker loop (untuk daemon) ──────────────────────────────────────────

def work_once(handler) -> bool:
    """Pop one job and run handler(job). Returns True if a job was processed."""
    job = pop(timeout=1)
    if not job:
        return False
    try:
        handler(job)
    except Exception:
        # Dead-letter on failure
        try:
            r = connect()
            r.lpush(DLQ_KEY, json.dumps({**job, "failed_at": time.time()}))
        except Exception:
            pass
    return True


def worker_loop(handler, idle_exit_after: int = 0) -> int:
    """Run worker until interrupted. Returns processed count on exit."""
    processed = 0
    while True:
        processed += work_once(handler)
    return processed
