"""Test V29.1 — SemanticRecall (TF-IDF hybrid recall)."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.semantic_recall import SemanticRecall
from aeryn_core.episodic_memory import EpisodicMemory


@pytest.fixture
def corpus(tmp_path):
    """Korpus 8 episode dengan topik berbeda."""
    path = tmp_path / "episodes.jsonl"
    eps = [
        ("baca Cargo.toml cari versi paket", ["fs_read"], True),
        ("web_search harga bitcoin hari ini", ["web_search"], True),
        ("http_get ambil judul halaman github", ["http_get"], False),
        ("fs_read parse package.json dependencies", ["fs_read"], True),
        ("cari tutorial rust async tokio", ["web_search"], True),
        ("read README.md project description", ["fs_read"], True),
        ("ambil data API cuaca jakarta", ["http_get"], True),
        ("parse toml config file versi dependency", ["fs_read"], True),
    ]
    with open(path, "w", encoding="utf-8") as f:
        for i, (goal, tools, ok) in enumerate(eps):
            f.write(json.dumps({
                "ts": time.time() - i * 3600,
                "session_id": f"s{i}",
                "goal": goal,
                "goal_tokens": sorted(set(
                    w for w in __import__("re").findall(r"[a-z0-9_.-]+", goal.lower())
                    if len(w) > 2)),
                "plan_source": "llm",
                "tools": tools,
                "ok": ok,
                "error": "",
                "lessons": [],
            }, ensure_ascii=False) + "\n")
    return str(path)


def test_semantic_finds_related_without_exact_words(corpus):
    """Goal tanpa kata persis sama tapi semantically related harus ketemu."""
    sr = SemanticRecall(corpus)
    # "versi" & "dependency" shared dgn episode Cargo.toml & toml config
    hits = sr.recall("cek versi dependency di file konfigurasi", k=3)
    assert hits, "semantic recall tidak boleh kosong"
    goals = [h["goal"] for h in hits]
    assert any("toml" in g.lower() or "versi" in g.lower() or
               "cargo" in g.lower() or "package.json" in g.lower()
               for g in goals)


def test_hybrid_ranks_exact_match_first(corpus):
    """Keyword exact match harus tetap dominan di posisi atas."""
    sr = SemanticRecall(corpus)
    hits = sr.recall("baca Cargo.toml cari versi paket", k=3)
    assert hits
    assert "Cargo.toml" in hits[0]["goal"]


def test_small_corpus_falls_back_keyword(tmp_path):
    """Korpus < MIN_CORPUS → keyword-only mode tetap jalan."""
    path = tmp_path / "small.jsonl"
    with open(path, "w") as f:
        f.write(json.dumps({
            "ts": time.time(), "session_id": "s0",
            "goal": "baca Cargo.toml versi",
            "goal_tokens": ["cargo.toml", "versi"],
            "tools": [], "ok": True, "error": "", "lessons": [],
        }) + "\n")
    sr = SemanticRecall(str(path))
    hits = sr.recall("Cargo.toml versi berapa")
    assert len(hits) == 1


def test_episodic_memory_uses_semantic_recall(tmp_path):
    """Integrasi: EpisodicMemory.recall kini lewat SemanticRecall."""
    m = EpisodicMemory(episode_dir=str(tmp_path / "eps"))
    m.record("s1", "baca Cargo.toml cari versi paket", "heuristic",
             [{"type": "tool", "name": "fs_read"}], answer="0.1.0")
    m.record("s2", "web_search bitcoin", "llm",
             [{"type": "tool", "name": "web_search"}], answer="harga")
    hits = m.recall("versi paket cargo")
    assert any("Cargo" in h.get("goal", "") for h in hits)
