"""V36: Test event bus ala OpenHands — pub/sub, wildcard, thread-safety,
ring buffer cap, watchdog threshold, isolasi exception subscriber."""

import threading

from aeryn_core.event_bus import (
    BUS,
    EVENT_ERROR,
    EVENT_FINAL,
    EVENT_HISTORY,
    EVENT_PLAN,
    EVENT_TIMEOUT,
    EVENT_TOOL,
    EventBus,
    HealthWatchdog,
)


def test_constants_are_string_literals():
    # Event typed = string literal sederhana
    assert EVENT_PLAN == "plan"
    assert EVENT_TOOL == "tool"
    assert EVENT_FINAL == "final"
    assert EVENT_ERROR == "error"
    assert EVENT_TIMEOUT == "timeout"
    assert EVENT_HISTORY == "history"


def test_basic_pubsub_exact_match():
    bus = EventBus()
    got = []
    bus.subscribe(EVENT_FINAL, lambda et, d: got.append((et, d)))
    bus.publish(EVENT_FINAL, {"answer": "halo"})
    bus.publish(EVENT_PLAN, {})  # jenis lain: tidak diterima subscriber ini
    assert got == [(EVENT_FINAL, {"answer": "halo"})]


def test_wildcard_subscribe_receives_all_types():
    bus = EventBus()
    got = []
    bus.subscribe("*", lambda et, d: got.append(et))
    for et in (EVENT_PLAN, EVENT_TOOL, EVENT_FINAL, EVENT_ERROR):
        bus.publish(et, {})
    assert got == [EVENT_PLAN, EVENT_TOOL, EVENT_FINAL, EVENT_ERROR]


def test_thread_safety_publish_from_many_threads():
    bus = EventBus()
    received = []
    lock = threading.Lock()

    def cb(et, d):
        with lock:
            received.append(d["i"])

    bus.subscribe("*", cb)

    n_threads, per_thread = 8, 50

    def worker(offset):
        for i in range(per_thread):
            bus.publish(EVENT_TOOL, {"i": offset * per_thread + i})

    threads = [
        threading.Thread(target=worker, args=(t,)) for t in range(n_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(received) == n_threads * per_thread
    assert sorted(received) == list(range(n_threads * per_thread))


def test_ring_buffer_history_cap():
    bus = EventBus(history_cap=5)
    for i in range(10):
        bus.publish(EVENT_ERROR, {"n": i})
    recent = bus.recent(event_type=EVENT_ERROR, limit=50)
    assert len(recent) == 5  # cap ring buffer bekerja
    assert [r["data"]["n"] for r in recent] == [5, 6, 7, 8, 9]  # terakhir N


def test_recent_mixed_and_limit():
    bus = EventBus()
    bus.publish(EVENT_FINAL, {"a": 1})
    bus.publish(EVENT_TIMEOUT, {"b": 2})
    bus.publish(EVENT_PLAN, {"c": 3})  # plan tidak masuk history (tidak penting)
    mixed = bus.recent(limit=10)
    kinds = {r["event"] for r in mixed}
    assert kinds == {EVENT_FINAL, EVENT_TIMEOUT}
    limited = bus.recent(limit=1)
    assert len(limited) == 1 and limited[0]["event"] == EVENT_TIMEOUT


def test_watchdog_threshold():
    bus = EventBus()
    wd = HealthWatchdog(bus, window=100, threshold=0.40)
    assert wd.unhealthy() is False  # belum ada data → sehat

    # 30 error dari 100 event = 30% → masih sehat
    for i in range(70):
        bus.publish(EVENT_TOOL, {})
    for i in range(30):
        bus.publish(EVENT_ERROR, {})
    assert wd.error_rate() < 0.40
    assert wd.unhealthy() is False

    # 1 error lagi → 31/100... masih sehat; dorong ke >=40%
    for i in range(9):
        bus.publish(EVENT_ERROR, {})
    # window sekarang: terakhir 100 event berisi error lebih banyak
    # total error 39 + tool 70 → jendela 100 terakhir campuran; hitung eksplisit:
    while not wd.unhealthy():
        bus.publish(EVENT_ERROR, {})
    assert wd.error_rate() >= 0.40


def test_subscriber_exception_does_not_break_publisher():
    bus = EventBus()

    def bad_cb(et, d):
        raise RuntimeError("subscriber rusak")

    got = []
    bus.subscribe(EVENT_FINAL, bad_cb)
    bus.subscribe(EVENT_FINAL, lambda et, d: got.append(d))
    # Tidak boleh raise; subscriber kedua tetap menerima event.
    bus.publish(EVENT_FINAL, {"ok": True})
    assert got == [{"ok": True}]

    # Wildcard subscriber rusak juga tidak menghentikan publish berikutnya.
    bus.subscribe("*", bad_cb)
    bus.publish(EVENT_ERROR, {"ok": True})
    assert bus.stats()["published"][EVENT_ERROR] == 1


def test_global_singleton_bus_exists():
    # Singleton global siap dipakai modul lain / wiring daemon
    assert isinstance(BUS, EventBus)
