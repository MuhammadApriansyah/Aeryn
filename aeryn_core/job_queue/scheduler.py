"""V61.1 — Cron Scheduler (integrasi fitur Hermes: jadwal berulang).

Scheduler cron mandiri di atas PostgreSQL (via neon_db), memakai `croniter`
utk hitung next-run dari ekspresi cron 5-field ("0 9 * * *").

Fitur:
- CRUD job (add / list / toggle / delete).
- Background loop: tiap N detik cek job yg waktunya tiba → fire action
  (HTTP request ke URL, method + payload) → catat run (SUCCESS/FAIL + durasi).
- Bitemporal-friendly: riwayat run tersimpan utk audit.

Action dijalankan sebagai HTTP webhook (post ke url yg didaftarkan) — jujur,
umum, & mudah diuji lokal (bisa arahkan ke endpoint sendiri).
"""
from __future__ import annotations

import threading
import time
import json
import uuid
from datetime import datetime, timedelta
from urllib import request as urllib_request
from urllib.error import URLError


def _now():
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


class CronScheduler:
    def __init__(self, db=None, poll_interval=10):
        from aeryn_core.database.neon_db import get_neon
        self.db = db or get_neon()
        self.poll = max(2, int(poll_interval))
        self._stop = threading.Event()
        self._thread = None
        self._ensure_schema()

    def _ensure_schema(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS cron_jobs ("
            "id TEXT PRIMARY KEY, name TEXT NOT NULL, "
            "schedule TEXT NOT NULL, action_url TEXT NOT NULL, "
            "method TEXT DEFAULT 'POST', payload JSONB, enabled BOOLEAN DEFAULT TRUE, "
            "last_run TIMESTAMP, next_run TIMESTAMP, run_count INTEGER DEFAULT 0, "
            "last_status TEXT, last_error TEXT, created_at TIMESTAMP DEFAULT now())")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS cron_runs ("
            "id TEXT PRIMARY KEY, job_id TEXT NOT NULL, status TEXT, "
            "duration_ms INTEGER, error TEXT, ran_at TIMESTAMP DEFAULT now())")

    # ── CRUD ────────────────────────────────────────────────

    def add_job(self, name, schedule, url, method="POST", payload=None) -> str:
        jid = uuid.uuid4().hex[:14]
        next_run = self._next_from(schedule)
        self.db.execute(
            "INSERT INTO cron_jobs (id,name,schedule,action_url,method,payload,enabled,next_run) "
            "VALUES (%s,%s,%s,%s,%s,%s,TRUE,%s)",
            (jid, name, schedule, url, method,
             json.dumps(payload or {}), (next_run.isoformat() if next_run else None)))
        return jid

    def list_jobs(self):
        rows = self.db.fetchall(
            "SELECT * FROM cron_jobs ORDER BY created_at DESC")
        return rows

    def toggle(self, jid, enabled):
        self.db.execute("UPDATE cron_jobs SET enabled=%s WHERE id=%s",
                        (bool(enabled), jid))

    def delete_job(self, jid):
        self.db.execute("DELETE FROM cron_jobs WHERE id=%s", (jid,))

    def get_runs(self, jid, limit=20):
        return self.db.fetchall(
            "SELECT status,duration_ms,error,ran_at FROM cron_runs "
            "WHERE job_id=%s ORDER BY ran_at DESC LIMIT %s", (jid, limit))

    # ── Scheduling ───────────────────────────────────────────

    def _next_from(self, schedule, base=None):
        try:
            from croniter import croniter
            return croniter(schedule, base or datetime.now()).get_next(datetime)
        except Exception:
            return (base or datetime.now()) + timedelta(days=1)

    def _fire(self, job) -> dict:
        """Execute a due job's action (HTTP) — return status record."""
        url = job.get("action_url")
        payload = job.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        method = (job.get("method") or "POST").upper()
        t0 = time.time()
        try:
            data = json.dumps(payload).encode()
            req = urllib_request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json")
            with urllib_request.urlopen(req, timeout=15) as r:
                r.read()
            return {"status": "SUCCESS", "duration_ms": int((time.time() - t0) * 1000), "error": None}
        except (URLError, Exception) as e:  # noqa
            return {"status": "FAIL", "duration_ms": int((time.time() - t0) * 1000),
                    "error": str(e)[:300]}

    def _tick(self):
        """Fire due & enabled jobs; update next_run + run log."""
        now = datetime.utcnow()
        jobs = self.list_jobs()
        for job in jobs:
            if not job.get("enabled"):
                continue
            nr = job.get("next_run")
            try:
                if nr and isinstance(nr, str):
                    nr = datetime.fromisoformat(nr.replace("Z", ""))
            except Exception:
                nr = None
            if nr and nr > now:
                continue
            res = self._fire(job)
            jid = job.get("id")
            self.db.execute(
                "UPDATE cron_jobs SET last_run=%s, last_status=%s, last_error=%s, "
                "run_count=coalesce(run_count,0)+1, next_run=%s WHERE id=%s",
                (_now(), res["status"], res["error"],
                 self._next_from(job.get("schedule")).isoformat(), jid))
            self.db.execute(
                "INSERT INTO cron_runs (id,job_id,status,duration_ms,error) VALUES (%s,%s,%s,%s,%s)",
                (uuid.uuid4().hex[:14], jid, res["status"], res["duration_ms"], res["error"]))

    def loop(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                import logging
                logging.getLogger("aeryn.cron").warning("tick: %s", e)
            self._stop.wait(self.poll)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self.loop, daemon=True, name="cron-scheduler")
        self._thread.start()

    def stop(self):
        self._stop.set()


_scheduler = None


def get_scheduler(poll_interval=10):
    global _scheduler
    if _scheduler is None:
        _scheduler = CronScheduler(poll_interval=poll_interval)
    return _scheduler