"""aeryn-native-scheduler daemon (RM4) — PROSES TERPISAH (runit).

Rust AerynScheduler (pyo3) jalan di thread native dalam PROSES INI —
bukan dalam proses API (GIL contention memblokir uvicorn).

Tugas:
- Tick loop (interval 60s): cron tick internal (job_queue._tick — job due → execute)
- Daily tick (86400s): decay_all (bitemporal facts + vault)
- State file: Personalisasi/Database/native_scheduler.json (health visibility
  untuk /scheduler/health endpoint API — dibaca dari file, bukan in-process)
"""

import json
import time
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/aeryn-core-agent")

STATE_PATH = "/data/data/com.termux/files/home/aeryn-core-agent/Personalisasi/Database/native_scheduler.json"


def _save_state(h: dict) -> None:
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(h, f)
    except Exception:
        pass


def main() -> None:
    from aeryn_core.platform.native_scheduler import NativeScheduler

    ns = NativeScheduler(poll_interval=60, daily_interval=86400)
    ns.start()
    print(f"[{time.strftime('%H:%M:%S')}] aeryn-native-scheduler started "
          f"(Rust native, poll 60s, daily 86400s)", flush=True)

    while True:
        time.sleep(15)  # tulis state tiap 15s (watchdog + API visibility)
        h = ns.health()
        # RM8_CONSOLIDATE: daily tick → konsolidasi pengalaman (pattern → skill)
        if h.get("last_daily_ago_s") is not None and h["last_daily_ago_s"] < 30:
            try:
                from aeryn_core.agent.experience_learning import consolidate_experience
                r = consolidate_experience("sen", min_frequency=3, max_crystallize=2)
                print(f"[{time.strftime('%H:%M:%S')}] experience consolidated: "
                      f"patterns={r.get('patterns', 0)}",
                      flush=True)
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] consolidate gagal: {str(e)[:120]}",
                      flush=True)
        h["pid"] = None  # diisi di bawah
        import os
        h["pid"] = os.getpid()
        _save_state(h)
        if h.get("errors"):
            print(f"[{time.strftime('%H:%M:%S')}] errors: {h['errors'][-1]}",
                  flush=True)


if __name__ == "__main__":
    main()
