"""Test V39.5 — LLM-as-Verifier.

Mechanical checks (tanpa LLM): leak marker, saran berbahaya.
LLM verify: stub model_client — rubrik JSON parse, degrade aman.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.verifier import (
    mechanical_checks, verify_answer, verify_with_llm)


class StubClient:
    """Model client palsu yang mengembalikan verdict JSON tertentu."""

    def __init__(self, content: str):
        self.content = content

    def chat(self, messages, tools=None, temperature=0.4, max_tokens=200):
        class R:
            choices = [type("C", (), {"message": {"content": self.content}})]

        return {"choices": R.choices}


def test_mechanical_catches_canary_leak():
    m = mechanical_checks("jawaban dengan [CANARY-a7x] bocor", [])
    assert m["issues"] and any("CANARY" in i for i in m["issues"])


def test_mechanical_catches_dangerous_advice():
    m = mechanical_checks("cara terbaik adalah rm -rf folder itu", [])
    assert m["issues"]


def test_mechanical_clean_passes():
    m = mechanical_checks("React adalah library UI", [
        {"type": "tool", "name": "web_search"}])
    assert not m["issues"]


def test_llm_verifier_pass():
    client = StubClient('{"pass": true, "reason": "konsisten"}')
    v = verify_answer(client, "jawaban bagus", "goal",
                      [{"type": "tool", "name": "web_search"}])
    assert v["pass"] and v["via"] == "llm"


def test_llm_verifier_fail_on_contradiction():
    client = StubClient(
        '{"pass": false, "reason": "angka tidak cocok dgn hasil tool"}')
    v = verify_answer(client, "hasilnya 42", "berapa 2+2?",
                      [{"type": "tool", "name": "math_calc"}])
    assert not v["pass"]
    # jawaban harus diganti pesan aman di daemon — di sini cukup cek reason


def test_llm_failure_degrades_gracefully():
    class Broken:
        def chat(self, *a, **kw):
            raise RuntimeError("provider down")

    v = verify_answer(Broken(), "jawaban normal", "goal",
                      [{"type": "tool", "name": "fs_read"}])
    assert v["pass"] and v["via"] == "degraded"


def test_no_tool_run_skips_llm():
    calls = []

    class Counting(StubClient):
        def chat(self, *a, **kw):
            calls.append(1)
            return super().chat(*a, **kw)

    v = verify_answer(Counting('{"pass": true}'), "halo juga!", "halo", [])
    assert v["via"] == "mechanical" and not calls
