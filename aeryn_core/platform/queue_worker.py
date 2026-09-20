#!/usr/bin/env python3
"""V61.4 — IN1: Redis queue worker daemon (runit service).

Pops jobs dari redis queue (aeryn:jobs) dan mengeksekusi handler.
Jobs tahan restart (persist di redis). Run via runit — auto-restart.
"""

import os
import sys
import signal

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from aeryn_core.platform import redis_queue as rq

_running = True


def _stop(signum, frame):
    global _running
    _running = False


signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT, _stop)


def handle_job(job: dict) -> None:
    """Execute one job. Real handlers — no test doubles."""
    jtype = job.get("type", "unknown")
    print(f"[worker] job {job.get('id')} type={jtype}", flush=True)

    if jtype == "chat":
        # Chat job: panggil endpoint chat Aeryn internal
        import urllib.request
        import urllib.error
        payload = json_dumps = __import__("json").dumps(
            {"goal": job.get("goal", ""), "user_id": job.get("user_id", "default")}
        ).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:3010/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode()
            print(f"[worker] chat result: {body[:200]}", flush=True)
    elif jtype == "shell":
        # Shell job: run command
        import subprocess
        out = subprocess.run(
            job.get("command", ""), shell=True,
            capture_output=True, text=True, timeout=120,
        )
        print(f"[worker] shell rc={out.returncode} out={out.stdout[:200]}", flush=True)
    else:
        print(f"[worker] unknown type {jtype} — skip", flush=True)


def main():
    print(f"[worker] Aeryn redis worker started (pid {os.getpid()})", flush=True)
    while _running:
        try:
            if not rq.ping():
                import time
                time.sleep(5)
                continue
            # G2: pindahkan job terjadwal yang waktunya tiba ke queue utama
            try:
                rq.poll_due()
            except Exception as _e:
                pass
            if not rq.work_once(handle_job):
                import time
                time.sleep(0.5)
        except Exception as e:
            print(f"[worker] loop error: {e}", flush=True)
            import time
            time.sleep(5)
    print("[worker] stopped cleanly", flush=True)


if __name__ == "__main__":
    main()
