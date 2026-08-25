"""Test V36 — LLM compaction riwayat sesi (load_with_compaction).

Cakupan:
(a) fallback aman tanpa llm_summarize,
(b) callable dipanggil & hasilnya di-cache (panggil 2x → callable 1x),
(c) cache kadaluarsa → ringkas ulang,
(d) callable yang raise / hasil invalid → fallback deterministik,
(e) regression: load() lama tetap berperilaku sama.
"""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core import session_history as sh


@pytest.fixture()
def sess(tmp_path, monkeypatch):
    """Arahkan DB sesi ke tmp agar tidak menyentuh data asli."""
    monkeypatch.setattr(sh, "_DB_DIR", str(tmp_path))
    return sh


def _seed(sid, n=6, size=500):
    """Isi sesi dengan n pasang user/assistant panjang (memaksa compaction)."""
    for i in range(n):
        sh.record(sid, "user", f"pertanyaan-{i} " + "x" * size)
        sh.record(sid, "assistant", f"jawaban-{i} " + "y" * size)


def _compact_cache_path(sid):
    return sh._compact_path(sid)


# (a) fallback aman tanpa llm_summarize
def test_fallback_without_llm(sess):
    sid = "v36-nollm"
    _seed(sid)
    out = sh.load_with_compaction(sid, char_budget=800)
    assert out, "harus tetap mengembalikan pesan"
    assert out[0]["role"] == "system"
    assert "[ringkasan" in out[0]["content"], "fallback deterministik"
    # tanpa llm_summarize, cache TIDAK boleh ditulis
    assert not os.path.exists(_compact_cache_path(sid))


# (b) callable dipanggil sekali & tercache
def test_llm_called_once_and_cached(sess):
    sid = "v36-cache"
    _seed(sid)
    calls = []

    def fake_llm(text):
        calls.append(text)
        return "RINGKASAN-LLM-1"

    out1 = sh.load_with_compaction(sid, char_budget=800,
                                   llm_summarize=fake_llm)
    assert len(calls) == 1
    assert "RINGKASAN-LLM-1" in out1[0]["content"]
    # teks yang dikirim ke LLM dibatasi ~4000 char
    assert len(calls[0]) <= 4000

    out2 = sh.load_with_compaction(sid, char_budget=800,
                                   llm_summarize=fake_llm)
    assert len(calls) == 1, "cache harus mencegah telepon LLM kedua"
    assert out2 == out1

    # file cache ada dengan field ts + summary
    with open(_compact_cache_path(sid)) as f:
        c = json.load(f)
    assert set(c) >= {"ts", "summary"}
    assert c["summary"] == "RINGKASAN-LLM-1"


# (c) cache kadaluarsa → ringkas ulang
def test_cache_expiry_recompacts(sess, monkeypatch):
    sid = "v36-expiry"
    _seed(sid)
    calls = []

    def fake_llm(text):
        calls.append(text)
        return f"RINGKASAN-VERSI-{len(calls)}"

    sh.load_with_compaction(sid, char_budget=800, llm_summarize=fake_llm)
    assert len(calls) == 1

    # kadaluarsakan cache: mundurkan ts melewati TTL (7 jam ke belakang)
    cp = _compact_cache_path(sid)
    with open(cp) as f:
        c = json.load(f)
    c["ts"] = time.time() - (sh.COMPACT_TTL + 3600)
    with open(cp, "w") as f:
        json.dump(c, f)

    sh.load_with_compaction(sid, char_budget=800, llm_summarize=fake_llm)
    assert len(calls) == 2, "cache kadaluarsa harus memicu ringkas ulang"
    with open(cp) as f:
        c2 = json.load(f)
    assert c2["summary"] == "RINGKASAN-VERSI-2"


# (d) callable raise / hasil invalid → fallback deterministik
def test_llm_exception_falls_back(sess):
    sid = "v36-raiser"
    _seed(sid)

    def boom(_text):
        raise RuntimeError("kuota habis")

    out = sh.load_with_compaction(sid, char_budget=800, llm_summarize=boom)
    assert out and "[ringkasan" in out[0]["content"], "fallback jalan"
    assert not os.path.exists(_compact_cache_path(sid)), \
        "kegagalan tidak boleh di-cache"


def test_llm_invalid_result_falls_back(sess):
    sid = "v36-invalid"
    _seed(sid)
    out = sh.load_with_compaction(sid, char_budget=800,
                                  llm_summarize=lambda t: None)
    assert "[ringkasan" in out[0]["content"]
    assert not os.path.exists(_compact_cache_path(sid))


def test_no_raise_on_corrupt_cache(sess):
    """Cache korup → diperlakukan seperti tidak ada, fallback aman."""
    sid = "v36-corrupt"
    _seed(sid)
    with open(_compact_cache_path(sid), "w") as f:
        f.write("{ini bukan json")
    out = sh.load_with_compaction(sid, char_budget=800,
                                  llm_summarize=lambda t: "OK")
    assert "OK" in out[0]["content"]


# (e) regression: load() lama tetap berperilaku sama
def test_load_regression_unchanged(sess):
    sid = "v36-regress"
    _seed(sid, n=4, size=300)
    out = sh.load(sid, char_budget=800)
    assert out[0]["role"] == "system"
    assert out[0]["content"].startswith("Riwayat awal sesi:\n[ringkasan")
    # turn terbaru utuh dan urut kronologis
    roles = [m["role"] for m in out[1:]]
    assert roles[-1] == "assistant"
    assert "jawaban-3" in out[-1]["content"]
    # load() tidak pernah menyentuh file cache kompaksi
    assert not os.path.exists(_compact_cache_path(sid))


def test_recent_turns_identical_between_load_and_compaction(sess):
    """Turn utuh (dalam budget) identik di load() vs load_with_compaction()."""
    sid = "v36-parity"
    _seed(sid, n=5, size=400)
    a = sh.load(sid, char_budget=900)
    b = sh.load_with_compaction(sid, char_budget=900,
                                llm_summarize=lambda t: "LLM")
    assert a[1:] == b[1:], "turn dalam budget harus identik"
