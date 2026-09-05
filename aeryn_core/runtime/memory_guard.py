"""Memory Guard — prevent OOM under load (P2 fix from STRESS_REPORT).

Gap 1 finding: server OOM-crashed under heavy load (limited proot RAM).
Two defenses:
  1. In-flight request semaphore — cap concurrent agent requests.
  2. RSS memory threshold — reject with 503 before we OOM.

Config via env (optional overrides):
  AERYN_MAX_INFLIGHT (default 10)
  AERYN_MAX_MEMORY_MB (default 400)
"""

import os
import asyncio
from typing import Tuple


def _process_rss_mb() -> float:
    """Current process RSS in MB (psutil, falls back to /proc)."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024
    except Exception:
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024
        except Exception:
            return 0.0
    return 0.0


def system_memory_mb() -> float:
    """Total system RAM in MB (best-effort)."""
    try:
        import psutil
        return psutil.virtual_memory().total / 1024 / 1024
    except Exception:
        return 0.0


class MemoryGuard:
    def __init__(self):
        self.max_inflight = int(os.environ.get("AERYN_MAX_INFLIGHT", "10"))
        self.max_memory_mb = float(os.environ.get("AERYN_MAX_MEMORY_MB", "400"))
        self._semaphore = asyncio.Semaphore(self.max_inflight)

    def check_memory(self) -> Tuple[bool, str]:
        """Return (ok, reason). ok=False means reject with 503."""
        rss = _process_rss_mb()
        if rss >= self.max_memory_mb:
            return False, f"memory pressure: {rss:.0f}MB >= {self.max_memory_mb:.0f}MB"
        return True, ""

    @property
    def semaphore(self) -> asyncio.Semaphore:
        return self._semaphore

    def status(self) -> dict:
        rss = _process_rss_mb()
        return {
            "rss_mb": round(rss, 1),
            "max_memory_mb": self.max_memory_mb,
            "max_inflight": self.max_inflight,
            "throttled": rss >= self.max_memory_mb,
        }


_guard = None


def get_memory_guard() -> MemoryGuard:
    global _guard
    if _guard is None:
        _guard = MemoryGuard()
    return _guard