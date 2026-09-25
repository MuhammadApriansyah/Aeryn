#!/data/data/com.termux/files/home/aeryn-venv/bin/python
"""aeryn-unified (v64) — SUPERVISOR SERVICE TUNGGAL.

Menggantikan 5 service runsv (api/worker/gateway/watchdog/native-scheduler)
menjadi SATU service: `aeryn`. Setiap komponen jalan sebagai subprocess yang
dikelola supervisor ini:

  api       : python -m apps.api.routers.main        (FastAPI :3010)
  worker    : python aeryn_core/platform/queue_worker.py
  gateway   : python aeryn_core/platform/gateway_bot.py (Discord)
  scheduler : python aeryn_core/platform/native_scheduler_daemon.py (Rust tick)
  watchdog  : python aeryn_core/platform/watchdog.py

Perilaku (runit-managed supervisor):
- Supervisor jalan di foreground (runsv restart bila supervisor mati).
- Tiap komponen: start → monitor; EXIT → restart setelah backoff (2s, 5s, 10s.. max 30s).
- stop/term → kirim SIGTERM ke semua anak, tunggu, lalu supervisor keluar
  (runit yang restart bila perlu; sv stop mematikan semuanya).
- Health state file: $PREFIX/var/run/aeryn-unified.json — dibaca watchdog
  dan /scheduler/health style checks.
- Log per komponen tetap ke file log lama (tee tidak perlu — anak menulis
  ke stdout supervisor + file).

Catatan memory: 1 runsv + 1 supervisor + 5 anak (tanpa 5 tee + 4 runsv
ekstra) — hemat ~15-20MB dan 9 proses lebih sedikit.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HOME = os.environ.get("HOME", str(Path.home()))
PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
REPO = os.path.join(HOME, "aeryn-core-agent")
VENV_PY = os.path.join(HOME, "aeryn-venv", "bin", "python")
LOG_DIR = os.path.join(PREFIX, "var", "log", "aeryn")
STATE_FILE = os.path.join(PREFIX, "var", "run", "aeryn-unified.json")

# komponen: nama → (cmd, argv, log_file)
COMPONENTS = {
    "api": ([VENV_PY, "-m", "apps.api.routers.main"], "aeryn-api.log"),
    "worker": ([VENV_PY, "aeryn_core/platform/queue_worker.py"], "aeryn-worker.log"),
    "gateway": ([VENV_PY, "aeryn_core/platform/gateway_bot.py"], "aeryn-gateway.log"),
    "scheduler": ([VENV_PY, "aeryn_core/platform/native_scheduler_daemon.py"],
                  "aeryn-native-scheduler.log"),
    "watchdog": ([VENV_PY, "aeryn_core/platform/watchdog.py"], "aeryn-watchdog.log"),
}

_procs: dict = {}
_backoff: dict = {}
_restarting: set = set()  # v64.1: single-flight restart (anti thread-pileup)
_shutting_down = False


def _write_state() -> None:
    """Health snapshot — dibaca endpoint + watchdog eksternal."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        state = {
            "supervisor_pid": os.getpid(),
            "started_at": time.time(),
            "components": {
                name: {
                    "pid": p.pid,
                    "alive": p.poll() is None,
                    "restarts": _backoff.get(name, {}).get("restarts", 0),
                }
                for name, p in _procs.items()
            },
        }
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_FILE)
    except Exception:
        pass  # state file tidak boleh bunuh supervisor


def _start(name: str) -> None:
    cmd, log_name = COMPONENTS[name]
    log_path = os.path.join(LOG_DIR, log_name)
    os.makedirs(LOG_DIR, exist_ok=True)
    log_f = open(log_path, "ab", buffering=0)
    p = subprocess.Popen(cmd, cwd=REPO, stdout=log_f, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL,
                         env=dict(os.environ))
    _procs[name] = p
    print(f"[unified] {name} start pid={p.pid}", flush=True)
    log_f.close()  # anak pegang fd-nya sendiri (fd diwariskan)


def _restart_with_backoff(name: str) -> None:
    """Anak mati → restart dengan backoff naik (2,5,10,20,30s).

    v64.1: single-flight — kalau restart name sudah berjalan, lewati
    (anti thread-pileup yang bikin spawn anak baru tiap poll cycle).
    """
    if name in _restarting:
        return  # sudah ada restart berjalan untuk komponen ini
    _restarting.add(name)
    try:
        b = _backoff.setdefault(name, {"next_delay": 2.0, "restarts": 0})
        delay = b["next_delay"]
        b["restarts"] += 1
        b["next_delay"] = min(b["next_delay"] * 2, 30.0)
        print(f"[unified] {name} exit — restart #{b['restarts']} dalam {delay:.0f}s", flush=True)
        time.sleep(delay)
        if not _shutting_down:
            _start(name)
            # sehat kembali: anak jalan >60s → reset backoff
            if name in _procs and _procs[name].poll() is None:
                def _reset_later():
                    time.sleep(60)
                    if name in _procs and _procs[name].poll() is None:
                        b["next_delay"] = 2.0
                import threading
                threading.Thread(target=_reset_later, daemon=True).start()
    finally:
        _restarting.discard(name)


def _shutdown(signum, frame):
    global _shutting_down
    if _shutting_down:
        return
    _shutting_down = True
    print(f"[unified] sinyal {signum} — stop semua anak...", flush=True)
    for name, p in _procs.items():
        if p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
    deadline = time.time() + 10
    for p in _procs.values():
        try:
            p.wait(timeout=max(0.1, deadline - time.time()))
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("[unified] semua anak berhenti — supervisor keluar", flush=True)
    sys.exit(0)


def main() -> int:
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    os.chdir(REPO)

    for name in COMPONENTS:
        _start(name)

    last_state = 0.0
    print(f"[unified] supervisor pid={os.getpid()} — {len(COMPONENTS)} komponen", flush=True)

    while True:
        time.sleep(2)
        # tulis state tiap 6s
        if time.time() - last_state > 6:
            _write_state()
            last_state = time.time()
        # monitor: anak mati → restart (di thread terpisah biar loop jalan)
        for name, p in list(_procs.items()):
            if p.poll() is not None:
                import threading
                threading.Thread(target=_restart_with_backoff, args=(name,),
                                daemon=True).start()


if __name__ == "__main__":
    sys.exit(main() or 0)
