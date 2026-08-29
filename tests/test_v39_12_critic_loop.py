"""Test V39.12 — Self-Refine Critic Loop."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety.critic_refine import (
    CRITIC_SOP,
    build_critic_sop,
    run_critic,
)


def test_critic_sop_contains_marker():
    assert "CRITIC MODE" in CRITIC_SOP
    assert "HASIL:" in CRITIC_SOP
    assert "ISSUES:" in CRITIC_SOP
    assert "CONFIDENCE:" in CRITIC_SOP


def test_build_critic_sop_injects_answer_and_trace():
    sop = build_critic_sop("hitung 2+2", "hasil 4",
                           [{"type": "tool", "name": "math_calc", "result_digest": "4"}])
    assert "hitung 2+2" in sop
    assert "hasil 4" in sop
    assert "math_calc" in sop
    assert "4" in sop


def test_build_critic_sop_handles_empty_trace():
    sop = build_critic_sop("halo", "hai", [])
    assert "tidak ada tool" in sop.lower() or "tidak ada" in sop


def test_run_critic_returns_issues_list():
    def mock_runner(sop, goal, session, mi, ws):
        return {
            "ok": True,
            "answer": (
                "HASIL: tidak ada kontradiksi\n"
                "STATUS: SELESAI\n"
                "ISSUES: \n"
                "CONFIDENCE: 95 — jawaban sederhana, konsisten"),
        }

    result = run_critic("test goal", "test answer", [], runner=mock_runner)
    assert result["ok"] is True
    assert isinstance(result["issues"], list)
    assert result["confidence"] == 95


def test_run_critic_parses_issues():
    def mock_runner(sop, goal, session, mi, ws):
        return {
            "answer": (
                "HASIL: ditemukan halusinasi\n"
                "STATUS: SELESAI\n"
                "ISSUES: model klaim install sukses tanpa tool, kontradiksi trace\n"
                "CONFIDENCE: 30"),
        }

    result = run_critic("install x", "berhasil", [], runner=mock_runner)
    assert len(result["issues"]) >= 1
    assert "halusinasi" in result["summary"] or any("halusinasi" in i for i in result["issues"])


def test_run_critic_handles_runner_error():
    def bad_runner(sop, goal, session, mi, ws):
        raise RuntimeError("provider down")

    result = run_critic("goal", "answer", [], runner=bad_runner)
    assert result["ok"] is False
    assert "provider down" in result["summary"] or "provider down" in result["raw"]


def test_run_critic_handles_missing_runner():
    result = run_critic("goal", "answer", [], runner=None)
    assert result["ok"] is False
    assert "runner unavailable" in result["summary"]
