"""RM4 Python driver — AerynScheduler (Rust) digabung: cron tick + decay.

Modul: aeryn_core/platform/native_scheduler.py
- Daemon jalan di thread native Rust (pyo3) — callback Python tiap tick:
  1) cron tick → job_queue.scheduler (cron_jobs PG due → execute via HTTP)
  2) daily tick → decay_all (facts bitemporal + vault)
- Stop/start/health eksplisit. Real API only — no test doubles.
"""

import json
import threading
import time

from aeryn_core.utils.llm_client import get_mode_router  # noqa: F401 (init chain)

_engine_mod = None


def _engine():
    global _engine_mod
    if _engine_mod is None:
        import aeryn_engine
        _engine_mod = aeryn_engine
    return _engine_mod


class NativeScheduler:
    """Scheduler daemon native Rust — cron tick + decay harian digabung."""

    def __init__(self, poll_interval: int = 60, daily_interval: int = 86400):
        self.poll_interval = poll_interval
        self.daily_interval = daily_interval
        self._thread: threading.Thread | None = None
        self._sched = None
        self.last_tick = 0.0
        self.last_daily = 0.0
        self.tick_count = 0
        self.errors: list = []

    # ── callback dari Rust daemon (tiap tick) ──
    def _on_tick(self, report_json: str) -> None:
        try:
            report = json.loads(report_json)
        except Exception:
            report = {"tick": True, "daily": False}
        self.tick_count += 1
        self.last_tick = time.time()

        # 1) CRON TICK — job due → execute (job_queue scheduler _tick)
        try:
            from aeryn_core.job_queue.scheduler import get_scheduler
            sched = get_scheduler(poll_interval=self.poll_interval)
            sched._tick()
        except Exception as e:
            self.errors.append(f"cron tick: {str(e)[:120]}")
            self.errors = self.errors[-20:]

        # 2) DAILY TICK — decay harian (bitemporal facts + vault)
        if report.get("daily"):
            self.last_daily = time.time()
            try:
                from aeryn_core.memory.memory_decay import get_memory_decay_engine
                d = get_memory_decay_engine()
                d.decay_all()
            except Exception as e:
                self.errors.append(f"decay daily: {str(e)[:120]}")
                self.errors = self.errors[-20:]

    # ── daemon lifecycle ──
    def start(self) -> bool:
        """Mulai daemon (thread Rust native — non-blocking)."""
        if self._thread and self._thread.is_alive():
            return False  # sudah jalan
        self._sched = _engine().AerynScheduler()
        t = threading.Thread(
            target=self._sched.run,
            args=(self._on_tick, self.poll_interval, self.daily_interval),
            daemon=True, name="aeryn-native-scheduler")
        self._thread = t
        t.start()
        return True

    def stop(self) -> bool:
        """Hentikan daemon."""
        if self._sched is None:
            return False
        was = self._sched.stop()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None
        return was

    def health(self) -> dict:
        """Status scheduler (untuk watchdog + /health)."""
        return {"running": bool(self._sched and self._sched.is_running()),
                "tick_count": self.tick_count,
                "last_tick_ago_s": round(time.time() - self.last_tick, 1) if self.last_tick else None,
                "last_daily_ago_s": round(time.time() - self.last_daily, 1) if self.last_daily else None,
                "poll_interval": self.poll_interval,
                "daily_interval": self.daily_interval,
                "errors": self.errors[-5:]}


_native = None


def get_native_scheduler(poll_interval: int = 60, daily_interval: int = 86400) -> NativeScheduler:
    global _native
    if _native is None:
        _native = NativeScheduler(poll_interval=poll_interval, daily_interval=daily_interval)
    return _native
