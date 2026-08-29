#!/usr/bin/env python3
"""Test V31.4 — MemoryCurator."""
import json
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.memory.memory_curator import MemoryCurator
import aeryn_core.platform.skill_forge as sf_module

def _jl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

def test_curate_strategies_arsip_basi(tmp_path):
    db = tmp_path / "db"
    now = time.time()
    refs = [
        {"ts": now - 60 * 86400, "ok": True, "findings": [], "recommendations": [], "strategy": "GOAL_SAM: lama"},
        {"ts": now - 3600, "ok": True, "findings": [], "recommendations": [], "strategy": ""},
    ]
    _jl(str(db / "reflections" / "reflections.jsonl"), refs)
    c = MemoryCurator(db_dir=str(db), archive_dir=str(tmp_path / "arch"))
    res = c.curate_strategies(now=now)
    assert res["archived"] == 1
    kept = [json.loads(l) for l in open(str(db / "reflections" / "reflections.jsonl"))]
    assert len(kept) == 1

def test_episode_tanpa_atom_tidak_dipangkas(tmp_path):
    db = tmp_path / "db"
    now = time.time()
    _jl(str(db / "episodes" / "episodes.jsonl"), [{"ts": now - 200 * 86400, "ok": True}])
    c = MemoryCurator(db_dir=str(db), archive_dir=str(tmp_path / "arch"))
    res = c.curate_episodes(now=now)
    assert res["pruned"] == 0 and "atom" in res["reason"]

def test_episode_lama_terpangkas_dengan_atom(tmp_path):
    db = tmp_path / "db"
    now = time.time()
    _jl(str(db / "episodes" / "episodes.jsonl"), [
        {"ts": now - 200 * 86400, "ok": True},
        {"ts": now - 200 * 86400, "ok": False},
        {"ts": now - 3600, "ok": True},
    ])
    _jl(str(db / "atoms" / "atoms.jsonl"), [{"ts": now, "x": 1}])
    c = MemoryCurator(db_dir=str(db), archive_dir=str(tmp_path / "arch"))
    res = c.curate_episodes(now=now)
    assert res["pruned"] == 1

def test_dedup_skill_fingerprint_sama(tmp_path):
    db = tmp_path / "db"
    skills = [
        {"id": "a", "fingerprint": "fs_read+versi", "occurrences": 3},
        {"id": "b", "fingerprint": "fs_read+versi", "occurrences": 7},
        {"id": "c", "fingerprint": "web_search+berita", "occurrences": 4},
    ]
    sf_dir = str(db / "skills")
    _jl(os.path.join(sf_dir, "skills.jsonl"), skills)
    c = MemoryCurator(db_dir=str(db), archive_dir=str(tmp_path / "arch"))
    old = sf_module.SKILL_DIR
    sf_module.SKILL_DIR = sf_dir
    try:
        res = c.curate_skills()
    finally:
        sf_module.SKILL_DIR = old
    assert res["removed"] == 1 and res["after"] == 2

def test_run_all_gagal_melembut(tmp_path):
    c = MemoryCurator(db_dir=str(tmp_path / "kosong"), archive_dir=str(tmp_path / "arch"))
    out = c.run_all()
    assert "strategies" in out and "skills" in out
