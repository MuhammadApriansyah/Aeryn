"""Test V39.10c — verifier cost gate + nightly summary cap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety.verifier import verify_answer


class Counting:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None, temperature=0.4, max_tokens=200):
        self.calls += 1

        class C:
            message = {"content": '{"pass": true, "reason": "ok"}'}

        class R:
            choices = [C()]

        return R()


def test_simple_local_tool_skips_llm(tmp_path=None):
    c = Counting()
    trace = [{"type": "tool", "name": "fs_read"}]
    v = verify_answer(c, "jawaban", "goal", trace)
    assert c.calls == 0 and v["via"] == "mechanical"


def test_factual_tool_still_deep_verified():
    c = Counting()
    trace = [{"type": "tool", "name": "web_search"}]
    verify_answer(c, "jawaban", "goal", trace)
    assert c.calls == 1


def test_complex_run_deep_verified():
    c = Counting()
    trace = [{"type": "tool", "name": n} for n in
             ("fs_read", "math_calc", "terminal")]
    verify_answer(c, "jawaban", "goal", trace)
    assert c.calls == 1


def test_nightly_summary_capped():
    import ast
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),
        "scripts", "nightly_reflection.py")).read()
    assert "[:600]" in src, "summary harus ada cap 600 char"
