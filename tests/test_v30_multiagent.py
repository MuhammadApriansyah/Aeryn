"""Test V30.2 — MultiAgentRunner: paralel worker, fail-soft, merge."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeTools:
    tools = {"fs_read": {"tier": "safe", "status": "native",
                         "success": 10, "fail": 0}}

    def schemas(self):
        return []


class FakeGate:
    def evaluate(self, *a, **k):
        return {"allowed": True}


class FakeShadow:
    def run_with_shadow(self, fn, args):
        return {"ok": True, "fn": fn}


class FakeModelOK:
    """Model yang langsung jawab final (tanpa tool call)."""
    def chat(self, messages, tools=None, **k):
        return {"choices": [{"message": {
            "content": f"selesai: {messages[1]['content'][:20]}",
            "tool_calls": None}}]}


class FakeModelOneToolThenDone:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None, **k):
        self.calls += 1
        if "tool" not in [m.get("role") for m in messages]:
            return {"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "t1", "function": {"name": "fs_read",
                 "arguments": '{"path": "/etc/hostname"}'}}]}}]}
        return {"choices": [{"message": {"content": "hasil dibaca",
                                         "tool_calls": None}}]}


class FakeModelFail:
    def chat(self, *a, **k):
        raise RuntimeError("provider down")


def _runner(model):
    from aeryn_core.multi_agent import MultiAgentRunner
    return MultiAgentRunner(model, FakeTools(), FakeGate(), FakeShadow(),
                            max_workers=3)


PLAN2 = {"subgoals": [
    {"step": 0, "desc": "baca file A", "tool_hint": "fs_read"},
    {"step": 1, "desc": "baca file B", "tool_hint": "fs_read"},
]}


def test_parallel_two_subgoals():
    r = _runner(FakeModelOK()).run_parallel(PLAN2, "sess_test")
    assert r["parallel"] is True
    assert r["workers"] == 2
    assert r["success"] == 2


def test_single_subgoal_skip_parallel():
    plan = {"subgoals": [{"step": 0, "desc": "satu saja"}]}
    r = _runner(FakeModelOK()).run_parallel(plan, "sess_x")
    assert r["parallel"] is False


def test_worker_dengan_tool_call():
    r = _runner(FakeModelOneToolThenDone()).run_parallel(PLAN2, "sess_t")
    assert r["success"] == 2
    assert all("dibaca" in res["answer"] for res in r["results"])


def test_fail_soft_satu_worker_gagal():
    r = _runner(FakeModelFail()).run_parallel(PLAN2, "sess_f")
    assert r["parallel"] is True
    assert r["success"] == 0
    assert all(res.get("error") for res in r["results"])


def test_merge_for_final_format():
    pout = {"parallel": True, "wall_s": 1.2, "workers": 2, "success": 2,
            "results": [
                {"subgoal": "A", "ok": True, "answer": "isi A"},
                {"subgoal": "B", "ok": False, "error": "gagal B"}]}
    merged = _runner(None).merge_for_final(pout)
    assert "✅" in merged and "❌" in merged
    assert "wall 1.2s" in merged


def test_merge_non_parallel_kosong():
    assert _runner(None).merge_for_final({"parallel": False}) == ""
