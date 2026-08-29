"""V36: Event bus internal ala OpenHands — satu hub pub/sub untuk semua interaksi.

Semua interaksi daemon (plan/tool/final/error/timeout/history) dipublikasikan
sebagai typed event ke EventBus; komponen lain (HealthWatchdog, /metrics, dll.)
tinggal subscribe tanpa tahu satu sama lain.

Desain:
- Thread-safe via threading.Lock (daemon FastAPI multi-request).
- Callback dijalankan sinkron saat publish; exception di satu subscriber
  TIDAK menjatuhkan publisher (di-swallow dan dicatat).
- Ring buffer history per jenis penting (final/error/timeout) untuk introspeksi.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Konstanta event typed sederhana (string literal)
# ---------------------------------------------------------------------------
EVENT_PLAN = "plan"
EVENT_TOOL = "tool"
EVENT_FINAL = "final"
EVENT_ERROR = "error"
EVENT_TIMEOUT = "timeout"
EVENT_HISTORY = "history"

WILDCARD = "*"

# Jenis event yang masuk ring buffer history (untuk introspeksi).
IMPORTANT_TYPES = frozenset({EVENT_FINAL, EVENT_ERROR, EVENT_TIMEOUT})

# Ukuran default ring buffer per jenis event penting.
HISTORY_CAP = 500


class EventBus:
    """Hub pub/sub thread-safe ala OpenHands event stream.

    - publish(event_type, data): kirim event ke semua subscriber yang cocok
      (exact match + wildcard '*').
    - subscribe(event_type, callback): daftarkan callback(event_type, data).
    - recent(event_type=None, limit=50): introspeksi ring buffer history.
    """

    def __init__(self, history_cap: int = HISTORY_CAP):
        self._lock = threading.Lock()
        # event_type -> list[callback]; '*' = wildcard subscriber
        self._subs: Dict[str, List[Callable[[str, dict], None]]] = defaultdict(list)
        # Ring buffer per jenis event penting (final/error/timeout)
        self._history_cap = history_cap
        self._history: Dict[str, Deque[Tuple[float, dict]]] = defaultdict(
            lambda: deque(maxlen=self._history_cap)
        )
        # Statistik minimal: total publish per jenis
        self._counts: Dict[str, int] = defaultdict(int)

    # -- pub/sub -----------------------------------------------------------

    def subscribe(self, event_type: str, callback: Callable[[str, dict], None]) -> None:
        """Daftarkan callback(event_type, data) untuk satu jenis event atau '*'."""
        if not callable(callback):
            raise TypeError("callback harus callable")
        with self._lock:
            self._subs[event_type].append(callback)

    def publish(self, event_type: str, data: Optional[dict] = None) -> None:
        """Kirim event ke semua subscriber yang cocok (sinkron).

        Exception di satu subscriber tidak menghentikan subscriber lain
        maupun publisher itu sendiri.
        """
        data = data if data is not None else {}
        with self._lock:
            self._counts[event_type] += 1
            if event_type in IMPORTANT_TYPES:
                # snapshot data agar mutasi lanjutan caller tidak mengubah history
                self._history[event_type].append((time.time(), dict(data)))
            targets = list(self._subs.get(event_type, [])) + list(self._subs.get(WILDCARD, []))

        for cb in targets:
            try:
                cb(event_type, data)
            except Exception:
                # Subscriber bermasalah tidak boleh menjatuhkan publisher;
                # dibiarkan diam-diam (swallow) sesuai kontrak pub/sub.
                pass

    # -- introspeksi ---------------------------------------------------------

    def recent(
        self,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """Ambil N event terakhir dari ring buffer history.

        - event_type=None → gabungan semua jenis penting, urut waktu naik.
        - Hasil: list of {"ts", "event", "data"}.
        """
        with self._lock:
            if event_type is not None:
                items = [(t, event_type, d) for (t, d) in self._history.get(event_type, ())]
            else:
                items = []
                for etype, deq in self._history.items():
                    for (t, d) in deq:
                        items.append((t, etype, d))
                items.sort(key=lambda x: x[0])
        return [
            {"ts": round(t, 3), "event": etype, "data": d}
            for (t, etype, d) in items[-limit:]
        ]

    def stats(self) -> dict:
        """Ringkasan kecil: jumlah publish per jenis + ukuran history."""
        with self._lock:
            return {
                "published": dict(self._counts),
                "history": {k: len(v) for k, v in self._history.items()},
                "subscribers": {
                    k: len(v) for k, v in self._subs.items() if v
                },
            }


class HealthWatchdog:
    """Subscriber bawaan: pantau error rate window terakhir N=100 event.

    Kalau error rate >= threshold (default 40%), unhealthy() → True.
    Dipakai nanti oleh endpoint /metrics.
    """

    def __init__(self, bus: EventBus, window: int = 100, threshold: float = 0.40):
        self.bus = bus
        self.window = window
        self.threshold = threshold
        self._lock = threading.Lock()
        # deque maxlen: hanya simpan status "apakah event ini error-ish"
        self._recent: Deque[bool] = deque(maxlen=window)
        # Subscribe ke SEMUA event penting + plan/tool supaya denominator window
        # mencerminkan aktivitas nyata (bukan cuma final/error/timeout).
        for etype in (
            EVENT_PLAN, EVENT_TOOL, EVENT_FINAL, EVENT_ERROR, EVENT_TIMEOUT,
        ):
            bus.subscribe(etype, self._on_event)

    def _on_event(self, event_type: str, _data: dict) -> None:
        with self._lock:
            self._recent.append(event_type in (EVENT_ERROR, EVENT_TIMEOUT))

    def error_rate(self) -> float:
        """Rasio error+timeout dalam window terakhir (0.0–1.0)."""
        with self._lock:
            n = len(self._recent)
            if n == 0:
                return 0.0
            return sum(1 for bad in self._recent if bad) / n

    def unhealthy(self) -> bool:
        """True kalau error rate window terakhir >= threshold."""
        return self.error_rate() >= self.threshold


# Singleton global ala RUN_STATS — modul lain tinggal import dan publish.
BUS = EventBus()
