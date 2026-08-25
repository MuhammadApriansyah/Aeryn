#!/usr/bin/env python3
"""
test_v37_nightly_organism.py — Test section `organism` nightly_reflection.

Semua sumber data di-mock via tmp_path + monkeypatch (fake health.json,
fake library dir, fake sqlite) — tidak menyentuh file asli.
"""
import json
import os
import sqlite3
import sys
import time

import pytest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import nightly_reflection as nr  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures: sumber data palsu di tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_health(tmp_path):
    path = tmp_path / "health" / "latest.json"
    path.parent.mkdir()
    data = {"generated_at": "2026-08-25T00:00:00+00:00", "results": {
        "NOUS/x": {"status": "OK", "latency_ms": 100},
        "GEMINI/y": {"status": "OK", "latency_ms": 200},
        "GROQ/z": {"status": "RATE_LIMITED", "latency_ms": 50},
        "OR/w": {"status": "CLIENT_ERROR", "latency_ms": 60},
    }}
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def fake_library(tmp_path):
    lib = tmp_path / "library"
    (lib / "a").mkdir(parents=True)
    now = time.time()
    # 2 entri baru, 1 lama, 1 non-md baru
    for rel, mtime in [("new1.md", now - 100), ("a/new2.md", now - 3600),
                       ("old.md", now - 200000)]:
        p = lib / rel
        p.write_text("x", encoding="utf-8")
        os.utime(p, (mtime, mtime))
    (lib / "notes.txt").write_text("bukan md", encoding="utf-8")
    return str(lib)


@pytest.fixture
def fake_pitfalls_db(tmp_path):
    db = tmp_path / "memory_graph.db"
    con = sqlite3.connect(str(db))
    con.execute("""CREATE TABLE pitfalls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signature TEXT, symptom TEXT, root_cause TEXT, fix TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    old = time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(time.time() - 3 * 86400))
    con.execute("INSERT INTO pitfalls (signature, created_at) "
                "VALUES ('lama', ?)", (old,))
    con.execute("INSERT INTO pitfalls (signature) VALUES ('baru')")
    con.commit()
    con.close()
    return str(db)


@pytest.fixture
def fake_state_db(tmp_path):
    db = tmp_path / "state.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, role TEXT, "
                "content TEXT, timestamp REAL)")
    con.execute("CREATE TABLE sessions (id INTEGER PRIMARY KEY, "
                "last_activity_at REAL)")
    cutoff = time.time() - 86400
    # id menaik = pesan makin baru (seperti state.db asli)
    msgs = [("user", "pesan user lama sekali", cutoff - 100),
            ("user", "Tool ask_hermes untuk Aeryn: delegasi kerja",
             time.time() - 20),
            ("assistant", "siap", time.time() - 10),
            ("user", "balas satu kata: siap", time.time())]
    for i, (role, content, ts) in enumerate(msgs):
        con.execute("INSERT INTO messages VALUES (?,?,?,?)",
                    (i + 1, role, content, ts))
    con.execute("INSERT INTO sessions VALUES (1, ?)", (time.time(),))
    con.execute("INSERT INTO sessions VALUES (2, ?)", (cutoff - 500,))
    con.commit()
    con.close()
    return str(db)


# ---------------------------------------------------------------------------
# Kolektor individual — happy path
# ---------------------------------------------------------------------------

def test_provider_health_summary(fake_health):
    ph = nr.provider_health(fake_health)
    assert ph["total_providers"] == 4
    assert ph["ok"] == 2
    assert ph["summary"] == "2/4 OK"
    assert ph["by_status"]["RATE_LIMITED"] == 1


def test_library_activity_counts_recent_md_only(fake_library):
    res = nr.library_activity(fake_library)
    assert res["new_entries_24h"] == 2


def test_pitfalls_count(fake_pitfalls_db):
    res = nr.pitfalls_count(fake_pitfalls_db)
    assert res["total"] == 2
    assert res["new_24h"] == 1


def test_hermes_activity(fake_state_db):
    res = nr.hermes_activity(fake_state_db)
    assert res["active_sessions_24h"] == 1
    heads = res["recent_user_messages"]
    # 3 pesan user terbaru berdasarkan id DESC (pesannya sendiri ada 3)
    assert heads == ["balas satu kata: siap",
                     "Tool ask_hermes untuk Aeryn: delegasi kerja",
                     "pesan user lama sekali"]


# ---------------------------------------------------------------------------
# Fail-soft: satu sumber gagal → "tidak tersedia", bukan crash
# ---------------------------------------------------------------------------

def test_provider_health_missing(tmp_path):
    res = nr.collect_organism(health_path=str(tmp_path / "nope.json"),
                              library_dir=str(tmp_path),
                              pitfalls_db=str(tmp_path / "no.db"),
                              state_db=str(tmp_path / "no.db"))
    assert res["provider_health"]["status"] == nr.UNAVAILABLE


def test_collect_organism_all_fail_soft(tmp_path):
    kosong = str(tmp_path / "kosong")  # tidak ada sama sekali
    res = nr.collect_organism(health_path=kosong,
                              library_dir=kosong,
                              pitfalls_db=kosong,
                              state_db=kosong)
    assert res["library"]["status"] == nr.UNAVAILABLE
    assert res["pitfalls"]["status"] == nr.UNAVAILABLE
    assert res["hermes"]["status"] == nr.UNAVAILABLE


def test_hermes_activity_wrong_schema(tmp_path):
    """Skema beda → fail-soft 'tidak tersedia', tidak raise."""
    db = tmp_path / "weird.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE pesan (teks TEXT)")
    con.commit()
    con.close()
    with pytest.raises(ValueError):
        nr.hermes_activity(str(db))          # kolektor mentah memang raise…
    res = nr.collect_organism(state_db=str(db),   # …tapi collect menelan
                              health_path=str(tmp_path / "x"),
                              library_dir=str(tmp_path),
                              pitfalls_db=str(tmp_path / "y"))
    assert res["hermes"]["status"] == nr.UNAVAILABLE


def test_empty_library_dir_ok(tmp_path):
    res = nr.library_activity(str(tmp_path))
    assert res["new_entries_24h"] == 0


# ---------------------------------------------------------------------------
# Digest organik
# ---------------------------------------------------------------------------

def _sample_report(runs=232, rate=81.4):
    return {"generated_at": "2026-08-25T03:00:00Z", "runs": runs,
            "success_rate_pct": rate,
            "top_tools": {"terminal": 5},
            "error_samples": [], "errors": 0}


def test_digest_contains_organic_bits():
    organism = {
        "library": {"new_entries_24h": 3},
        "provider_health": {"summary": "6/7 OK"},
        "pitfalls": {"total": 8, "new_24h": 2},
        "hermes": {"active_sessions_24h": 12},
    }
    report = _sample_report()
    report["organism"] = organism
    digest = nr.core_memory_digest(report)
    assert digest.startswith("Refleksi 2026-08-25:")
    assert "232 run, 81.4% sukses" in digest
    assert "lib+3" in digest
    assert "provider 6/7 OK" in digest
    assert "pitfall+2 (total 8)" in digest
    assert "Hermes aktif 12 sesi" in digest


def test_digest_with_unavailable_sources():
    report = _sample_report(runs=0)
    report["organism"] = {
        "library": {"status": nr.UNAVAILABLE},
        "provider_health": {"status": nr.UNAVAILABLE},
        "pitfalls": {"status": nr.UNAVAILABLE},
        "hermes": {"status": nr.UNAVAILABLE},
    }
    digest = nr.core_memory_digest(report)
    assert "tidak ada run" in digest
    assert "lib+" not in digest and "provider" not in digest


def test_handoff_summary_includes_org_bits():
    report = _sample_report()
    report["organism"] = {"library": {"new_entries_24h": 26},
                          "provider_health": {},
                          "pitfalls": {}, "hermes": {}}
    summary = nr.handoff_summary(report)
    assert "lib+26" in summary


# ---------------------------------------------------------------------------
# CLI: flag lama tetap kompatibel; end-to-end dengan semua path di-mock
# ---------------------------------------------------------------------------

def test_main_end_to_end_compat(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(nr, "EPISODES", str(tmp_path / "none.jsonl"))
    monkeypatch.setattr(nr, "OUT_DIR", str(tmp_path / "nightly"))
    monkeypatch.setattr(nr, "HANDOFF", str(tmp_path / "no-handoff.py"))
    monkeypatch.setattr(nr, "HEALTH_JSON", str(tmp_path / "no-health.json"))
    monkeypatch.setattr(nr, "LIBRARY_DIR", str(tmp_path))
    monkeypatch.setattr(nr, "PITFALLS_DB", str(tmp_path / "no.db"))
    monkeypatch.setattr(nr, "STATE_DB", str(tmp_path / "no.db"))
    monkeypatch.setattr(sys, "argv",
                        ["nightly_reflection.py", "--since-hours", "48",
                         "--no-handoff"])
    # core-memory asli jangan disentuh saat unit test
    import types
    fake_cm = types.ModuleType("aeryn_core.core_memory")
    class _CM:
        def raw(self):
            return {"context": ""}
        def edit(self, *a, **k):
            pass
    fake_cm.CoreMemory = _CM
    fake_pkg = types.ModuleType("aeryn_core")
    monkeypatch.setitem(sys.modules, "aeryn_core", fake_pkg)
    monkeypatch.setitem(sys.modules, "aeryn_core.core_memory", fake_cm)

    nr.main()
    out = json.loads(capsys.readouterr().out)
    report = json.load(open(out["report"], encoding="utf-8"))
    assert report["window_hours"] == 48.0
    assert "organism" in report
    org = report["organism"]
    assert set(org) == {"provider_health", "library", "pitfalls", "hermes"}
    for src in org.values():
        assert ("status" in src) or all(k in src for k in
                                        ("new_entries_24h",)) or \
               ("summary" in src) or ("new_24h" in src) or \
               ("active_sessions_24h" in src)
    # sumber yang tidak ada → fail-soft, bukan exception
    assert org["provider_health"].get("status") == nr.UNAVAILABLE
    assert org["pitfalls"].get("status") == nr.UNAVAILABLE
