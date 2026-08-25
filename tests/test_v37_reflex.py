"""V37 — Test refleks kontinuitas lintas-otak (hermes_reflex).

Semua test pakai sqlite db tmp buatan sendiri (skema tiruan meniru
messages di ~/.hermes/state.db). State.db asli TIDAK pernah disentuh.
"""

from __future__ import annotations

import os
import sqlite3
import time

import pytest

from aeryn_core import hermes_reflex as hr


SCHEMA = """
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    timestamp REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    compacted INTEGER NOT NULL DEFAULT 0
);
"""


def make_db(tmp_path, rows):
    """Buat db tmp dengan skema tiruan messages + insert rows."""
    p = str(tmp_path / "state.db")
    con = sqlite3.connect(p)
    con.executescript(SCHEMA)
    for sid, role, content, ts, active, compacted in rows:
        con.execute(
            "INSERT INTO messages (session_id, role, content, timestamp, active, compacted) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sid, role, content, ts, active, compacted),
        )
    con.commit()
    con.close()
    return p


NOW = time.time()


def test_baca_normal(tmp_path):
    """Pesan user terbaru terbaca, urut desc, format {ts, session_id, head}."""
    p = make_db(
        tmp_path,
        [
            ("s1", "user", "halo Aeryn\nbaris kedua", NOW - 60, 1, 0),
            ("s2", "assistant", "siap", NOW - 30, 1, 0),
            ("s3", "user", "pertanyaan lama", NOW - 100000, 1, 0),  # di luar window 6 jam
        ],
    )
    acts = hr.recent_hermes_activity(db_path=p)
    assert len(acts) == 1  # assistant & pesan lama tersaring
    a = acts[0]
    assert set(a.keys()) == {"ts", "session_id", "head"}
    assert a["session_id"] == "s1"
    assert "\n" not in a["head"]
    assert a["ts"] == pytest.approx(NOW - 60)


def test_db_kosong(tmp_path):
    """Db valid tapi tanpa pesan -> list kosong."""
    p = make_db(tmp_path, [])
    assert hr.recent_hermes_activity(db_path=p) == []
    assert hr.get_reflex_digest(db_path=p) == ""


def test_db_tak_ada(tmp_path):
    """Path tak ada -> [] tanpa raise."""
    p = str(tmp_path / "tidak_ada.db")
    assert hr.recent_hermes_activity(db_path=p) == []


def test_db_korup(tmp_path):
    """File korup (bukan sqlite) -> [] tanpa raise."""
    p = str(tmp_path / "korup.db")
    with open(p, "wb") as f:
        f.write(b"ini bukan database sqlite\x00\x01\x02")
    assert hr.recent_hermes_activity(db_path=p) == []
    # get_reflex_digest juga tidak boleh raise
    assert hr.get_reflex_digest(db_path=p) == ""


def test_skema_beda(tmp_path):
    """Tabel ada tapi kolom beda -> [] tanpa raise."""
    p = str(tmp_path / "beda.db")
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE messages (foo TEXT)")
    con.commit()
    con.close()
    assert hr.recent_hermes_activity(db_path=p) == []


def test_render_digest():
    """Digest berformat [Konteks lintas-otak] dan pakai head tiap item."""
    acts = [
        {"ts": NOW - 10, "session_id": "a", "head": "topik pertama"},
        {"ts": NOW - 5, "session_id": "b", "head": "topik kedua"},
    ]
    d = hr.render_activity_digest(acts)
    assert d.startswith("[Konteks lintas-otak]")
    assert "topik pertama" in d and "topik kedua" in d
    # Kosong -> string kosong
    assert hr.render_activity_digest([]) == ""
    assert hr.render_activity_digest([{"ts": 1, "session_id": "x", "head": ""}]) == ""


def test_batas_limit(tmp_path):
    """LIMIT dipatuhi: hanya N pesan terbaru yang kembali."""
    rows = [
        (f"s{i}", "user", f"pesan ke-{i}", NOW - i * 60, 1, 0)
        for i in range(10)
    ]
    p = make_db(tmp_path, rows)
    acts = hr.recent_hermes_activity(limit=3, db_path=p)
    assert len(acts) == 3
    heads = [a["head"] for a in acts]
    assert heads[0] == "pesan ke-0"  # terbaru dulu


def test_get_reflex_digest_max_panjang(tmp_path):
    """Digest gabungan max ~600 char."""
    long_text = "x" * 500 + " akhir"
    p = make_db(
        tmp_path,
        [("s", "user", long_text, NOW - 10, 1, 0)] * 8,
    )
    d = hr.get_reflex_digest(db_path=p)
    assert len(d) <= 600
    assert d.startswith("[Konteks lintas-otak]")


def test_read_only_connection(monkeypatch, tmp_path):
    """Koneksi dibuka read-only: write lewat koneksi itu harus ditolak."""
    p = make_db(tmp_path, [("s1", "user", "uji ro", NOW - 10, 1, 0)])
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("DELETE FROM messages")
    finally:
        con.close()


def test_default_path_env_override(monkeypatch, tmp_path):
    """DEFAULT_STATE_DB bisa dioverride via env (tanpa menyentuh db asli)."""
    p = make_db(tmp_path, [("s9", "user", "via env", NOW - 5, 1, 0)])
    monkeypatch.setenv("AERYN_HERMES_STATE_DB", p)
    # reload nilai default env di modul
    monkeypatch.setattr(hr, "DEFAULT_STATE_DB", p)
    acts = hr.recent_hermes_activity()
    assert len(acts) == 1 and acts[0]["session_id"] == "s9"
