"""Test suite Aeryn-Core — tanpa network, ModelClient di-mock.

Jalankan: cd ~/aeryn-core-agent && ./venv-proot/bin/python -m pytest tests/ -v
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.memory.episodic_memory import EpisodicMemory
from aeryn_core.reasoning.emotion_tone import tone_directive
from aeryn_core.safety.critic_pass import make_critic
from aeryn_core.reasoning.planner import _heuristic_plan, _looks_structured
from aeryn_core.reasoning.reflection import PostRunReflection


# ══════════ EpisodicMemory (V27.4) ══════════

def test_episodic_record_and_recall(tmp_path):
    """Record 2 episode → recall goal serupa menemukan yang relevan."""
    m = EpisodicMemory(episode_dir=str(tmp_path / "eps"))
    trace1 = [{"type": "tool", "name": "fs_read", "result_digest": "ok"}]
    trace2 = [{"type": "tool", "name": "web_search",
               "result_digest": "rate limit"}]
    m.record("s1", "baca Cargo.toml cari versi paket", "heuristic", trace1,
             answer="aeryn_native 0.1.0")
    m.record("s2", "web_search harga bitcoin hari ini", "llm", trace2,
             error="rate limit")
    hits = m.recall("baca Cargo.toml versi paket", k=3)
    assert len(hits) >= 1
    assert any("Cargo.toml" in h.get("goal", "") for h in hits)


def test_episodic_recall_empty_is_safe(tmp_path):
    m = EpisodicMemory(episode_dir=str(tmp_path / "none"))
    assert m.recall("apa pun") == []


def test_prompt_block_mentions_experience():
    block = EpisodicMemory.prompt_block(
        [{"goal": "uji sesuatu", "ok": True, "lessons": ["pelajaran A"]}])
    assert block.strip(), "prompt_block tidak boleh kosong utk episode valid"


def test_lessons_on_failure_and_timeout(tmp_path):
    m = EpisodicMemory(episode_dir=str(tmp_path / "eps"))
    ep = m.record("sx", "goal gagal timeout", "llm",
                  [{"type": "error", "detail": "boom"}],
                  timed_out=True)
    assert any("timeout" in l.lower() or "wall-budget" in l.lower()
               for l in ep.get("lessons", []))


# ══════════ PostRunReflection (V27.5) ══════════

def test_reflection_digest_runs_clean(tmp_path):
    r = PostRunReflection(reflection_dir=str(tmp_path / "refl"))
    digest = r.digest()
    assert isinstance(digest, dict)


def test_reflection_records_run(tmp_path):
    r = PostRunReflection(reflection_dir=str(tmp_path / "refl"))
    r.reflect(goal="uji refleksi", plan={"subgoals": [{"step": 0}]},
              trace=[{"type": "final"}], answer="selesai")
    digest = r.digest()
    assert digest.get("runs", 0) >= 1 or digest.get("total", 0) >= 1


# ══════════ EmotionTone (V27.7) ══════════

def test_tone_returns_str_for_neutral():
    out = tone_directive({"valence": 0.0, "arousal": 0.0})
    assert isinstance(out, str)


def test_tone_negative_aroused_is_direct():
    out = tone_directive({"valence": -0.6, "arousal": 0.9}).lower()
    assert out.strip() != ""
    # frustrasi harus mengarah ke gaya langsung/ringkas
    assert any(k in out for k in ("ringkas", "singkat", "langsung", "direct"))


# ══════════ Planner heuristik (V27.1) ══════════

def test_heuristic_plan_fs_read():
    subs = _heuristic_plan("fs_read /tmp/x.json lalu sebutkan isinya")
    assert len(subs) >= 1
    assert subs[0]["tool_hint"] == "fs_read"


def test_looks_structured_numbered_goal():
    assert _looks_structured("(1) baca file (2) jawab")
    assert not _looks_structured("halo dunia apa kabar")


# ══════════ CriticPass (V27.6) ══════════

class FakeCriticModel:
    """Balas verdict 'revise' dengan jawaban terkoreksi."""

    def chat(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        content = json.dumps({"verdict": "revise",
                              "issues": ["angka tidak cocok dengan bukti"],
                              "revised_answer": "versi 0.1.0"})
        return {"choices": [{"message": {"content": content}}]}


class FakeApproveModel:
    def chat(self, messages, tools=None, temperature=0.7, max_tokens=2048):
        content = json.dumps({"verdict": "approved", "issues": []})
        return {"choices": [{"message": {"content": content}}]}


def test_critic_revises_wrong_draft():
    critic = make_critic(FakeCriticModel())
    result = critic(draft_answer="versi 5.99",
                    tool_digests=["Cargo.toml: version = 0.1.0"])
    # hasil akhir harus memuat koreksi, bukan draft salah
    text = json.dumps(result, ensure_ascii=False).lower()
    assert "revise" in text and "5.99" not in str(result.get("answer", "")) \
        or result.get("answer") == "versi 0.1.0"


def test_critic_passes_good_draft():
    critic = make_critic(FakeApproveModel())
    result = critic(draft_answer="versi 0.1.0",
                    tool_digests=["Cargo.toml: version = 0.1.0"])
    assert result.get("answer") == "versi 0.1.0"


def test_critic_unparseable_keeps_draft():
    class Garbage:
        def chat(self, *a, **k):
            return {"choices": [{"message": {"content": "bukan json"}}]}

    critic = make_critic(Garbage())
    result = critic(draft_answer="draft asli",
                    tool_digests=["bukti"])
    assert result["answer"] == "draft asli"
