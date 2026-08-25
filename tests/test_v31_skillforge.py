"""Test V31.1 — SkillForge: distilasi episode → skill → matcher."""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.skill_forge import SkillForge


def _write_eps(path_dir, eps):
    os.makedirs(path_dir, exist_ok=True)
    with open(os.path.join(path_dir, "episodes.jsonl"), "w") as f:
        for e in eps:
            f.write(json.dumps(e) + "\n")


def _mk_ep(goal, tools, ok=True, error=None):
    return {"ts": time.time(), "session_id": "t", "goal": goal,
            "goal_tokens": sorted(goal.lower().split()),
            "tools": tools, "ok": ok,
            "error": error or "", "lessons": ([] if ok else ["validasi path"])}


def test_forge_butuh_min_occurrences(tmp_path):
    e = str(tmp_path / "e")
    _write_eps(e, [_mk_ep("baca Cargo.toml versi", ["fs_read"]),
                   _mk_ep("baca package.json versi", ["fs_read"])])  # cuma 2
    sf = SkillForge(episode_dir=e, skill_dir=str(tmp_path / "s"))
    assert sf.forge_from_episodes() == []


def test_forge_sukses_menghasilkan_skill(tmp_path):
    e = str(tmp_path / "e")
    eps = []
    for i in range(4):  # 4 episode serupa sukses + 1 gagal (rate 0.8)
        eps.append(_mk_ep(f"fs_read config{i}.toml cek versi dependency",
                          ["fs_read"], ok=(i < 3)))
    eps.append(_mk_ep("fs_read config9.toml cek versi",
                      ["fs_read"], ok=False))
    _write_eps(e, eps)
    sf = SkillForge(episode_dir=e, skill_dir=str(tmp_path / "s"))
    forged = sf.forge_from_episodes()
    assert len(forged) == 1
    sk = forged[0]
    assert sk["fingerprint"].startswith("fs_read+")
    assert sk["success_rate"] >= 0.6
    assert sk["steps"][0]["tool_hint"] == "fs_read"
    assert any("validasi" in p for p in sk["pitfalls"])


def test_forge_rate_rendah_ditolak(tmp_path):
    e = str(tmp_path / "e")
    eps = [_mk_ep("web_search berita A", ["web_search"], ok=(i < 1))
           for i in range(4)]  # rate 0.25
    _write_eps(e, eps)
    sf = SkillForge(episode_dir=e, skill_dir=str(tmp_path / "s"))
    assert sf.forge_from_episodes() == []


def test_tidak_duplikat_fingerprint(tmp_path):
    e = str(tmp_path / "e")
    eps = [_mk_ep("http_get api data i", ["http_get"]) for i in range(3)]
    _write_eps(e, eps)
    sf = SkillForge(episode_dir=e, skill_dir=str(tmp_path / "s"))
    first = sf.forge_from_episodes()
    second = sf.forge_from_episodes()
    assert len(first) == 1 and second == []


def test_match_goal_ke_skill(tmp_path):
    e = str(tmp_path / "e")
    s = str(tmp_path / "s")
    eps = [_mk_ep("fs_read toml file cek versi dependency", ["fs_read"])
           for _ in range(3)]
    _write_eps(e, eps)
    sf = SkillForge(episode_dir=e, skill_dir=s)
    sf.forge_from_episodes()
    hit = sf.match("tolong fs_read file toml proyek, versi berapa dependency-nya")
    assert hit is not None
    assert hit["tools"] == ["fs_read"]
    # goal tak nyambung → None
    assert sf.match("web_search cuaca jakarta hari ini") is None


def test_plan_from_skill_bentuk_benar(tmp_path):
    skill = {"id": "fs_read_versi", "fingerprint": "fs_read+versi",
             "trigger_tokens": ["toml", "versi"],
             "steps": [{"step": 0, "tool_hint": "fs_read",
                        "done_when": "ok"}],
             "tools": ["fs_read"], "success_rate": 1.0,
             "occurrences": 3, "sample_goal": "baca toml",
             "pitfalls": ["validasi path"], "ts": time.time()}
    plan = SkillForge.plan_from_skill(skill)
    assert plan["source"] == "skill"
    assert plan["skill_id"] == "fs_read_versi"
    assert plan["pitfalls"] == "validasi path"
    assert plan["subgoals"][0]["desc"].startswith("[skill]")
