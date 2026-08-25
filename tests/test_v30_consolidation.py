"""Test V30.1 — MemoryConsolidation: episode tua → knowledge atoms."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.memory_consolidation import MemoryConsolidator


def _write_episodes(path_dir, n, age_h=48.0, ok_ratio=0.7):
    """Tulis n episode dummy berumur age_h jam."""
    os.makedirs(path_dir, exist_ok=True)
    now = time.time()
    with open(os.path.join(path_dir, "episodes.jsonl"), "w") as f:
        for i in range(n):
            f.write(json.dumps({
                "ts": now - age_h * 3600,
                "session_id": f"s{i}",
                "goal": f"fs_read file{i}.json baca data",
                "goal_tokens": ["fs_read", f"file{i}.json"],
                "plan_source": "heuristic",
                "tools": ["fs_read"] if i % 3 else ["web_search"],
                "ok": i < int(n * ok_ratio),
                "error": "" if i < int(n * ok_ratio) else "tool gagal",
                "lessons": ["validasi path" if not i % 5 else "hemat iterasi"],
            }) + "\n")


def test_should_consolidate_butuh_minimum(tmp_path):
    c = MemoryConsolidator(episode_dir=str(tmp_path / "e"),
                           atom_dir=str(tmp_path / "a"))
    assert not c.should_consolidate()   # korpus kosong


def test_consolidate_menghasilkan_atom(tmp_path):
    e, a = tmp_path / "e", tmp_path / "a"
    _write_episodes(str(e), 60)         # 60 episode tua
    c = MemoryConsolidator(episode_dir=str(e), atom_dir=str(a))
    res = c.consolidate()
    assert res["consolidated"] is True
    assert res["episodes_summarized"] > 0
    # atom tersimpan
    atoms = c.load_atoms()
    assert len(atoms) == 1
    atom = atoms[0]
    assert 0 <= atom["success_rate"] <= 1
    assert atom["common_goals"]
    assert atom["tool_track"]


def test_consolidate_kedua_tidak_duplikat(tmp_path):
    e, a = tmp_path / "e", tmp_path / "a"
    _write_episodes(str(e), 60)
    c = MemoryConsolidator(episode_dir=str(e), atom_dir=str(a))
    c.consolidate()
    res2 = c.consolidate()              # cursor sudah maju → skip
    assert res2["consolidated"] is False


def test_episode_baru_tidak_ikut_dikonsolidasi(tmp_path):
    e, a = tmp_path / "e", tmp_path / "a"
    _write_episodes(str(e), 55)
    # tambah 5 episode SEGAR (umur 1 jam)
    now = time.time()
    with open(os.path.join(str(e), "episodes.jsonl"), "a") as f:
        for i in range(5):
            f.write(json.dumps({"ts": now - 3600, "session_id": f"f{i}",
                                "goal": "fresh goal", "tools": [],
                                "ok": True}) + "\n")
    c = MemoryConsolidator(episode_dir=str(e), atom_dir=str(a))
    res = c.consolidate(force=True)
    # episode segar tidak masuk window konsolidasi pertama (cursor 0..50)
    assert res["consolidated"] is True
    atoms = c.load_atoms()
    assert all(a2["window"]["to"] < now - 3600 * 20 for a2 in atoms)


def test_load_atoms_kosong_aman(tmp_path):
    c = MemoryConsolidator(episode_dir=str(tmp_path / "e"),
                           atom_dir=str(tmp_path / "a"))
    assert c.load_atoms() == []
