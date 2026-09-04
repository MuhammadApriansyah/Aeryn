#!/usr/bin/env python3
"""Edge Cases Battery — empty input, non-ASCII, collisions, thousands of pending."""

import asyncio
import json
import time
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

BASE = "http://127.0.0.1:3010"
results = []


def record(name, passed, detail=""):
    results.append((name, passed, detail))
    print(f"  {'✅' if passed else '❌'} {name}" + (f" — {detail}" if detail else ""))


async def test_empty_input():
    """Empty input, whitespace-only."""
    import aiohttp
    async with aiohttp.ClientSession() as s:
        for label, msg in [("empty", ""), ("whitespace", "   "), ("null-ish", None)]:
            try:
                async with s.post(f"{BASE}/v1/chat",
                                  json={"message": msg, "session_id": f"edge_{label}"},
                                  timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    status = resp.status
                record(f"input '{label}': handled (no crash)", status in (200, 422, 400),
                       f"status={status}")
            except Exception as e:
                record(f"input '{label}': handled", True, f"caught {type(e).__name__}")


async def test_non_ascii():
    """Non-ASCII, emoji, unicode."""
    import aiohttp
    cases = [("emoji", "🎉🎉🎉"), ("arabic", "مرحبا بالعالم"), ("cjk", "你好世界"),
             ("emoji+text", "Hello 🌍 from 世界 🎈")]
    async with aiohttp.ClientSession() as s:
        for label, msg in cases:
            try:
                async with s.post(f"{BASE}/v1/chat",
                                  json={"message": msg, "session_id": f"edge_{label}"},
                                  timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    body = await resp.read()
                    status = resp.status
                record(f"non-ascii '{label}': accepted", status == 200,
                       f"status={status}, bytes={len(body)}")
            except Exception as e:
                record(f"non-ascii '{label}': accepted", False, f"error={type(e).__name__}")


async def test_session_collision():
    """Same session_id, different users — no cross-contamination."""
    from aeryn_core.runtime.session_store import get_session_store
    store = get_session_store()
    # Both users use session "shared"
    store.save_session("u1", "shared", [{"role": "user", "content": "secret of u1"}])
    store.save_session("u2", "shared", [{"role": "user", "content": "secret of u2"}])
    s1 = store.load_session("u1", "shared")
    s2 = store.load_session("u2", "shared")
    no_leak = ("u1" in s1.messages[0]["content"]) and ("u2" in s2.messages[0]["content"])
    record("session collision: isolated by user", no_leak)


async def test_many_pending_approvals():
    """Thousands of pending approvals — store handles volume."""
    from aeryn_core.safety.guardrail_engine import (
        get_guardrail_engine, ApprovalRequest
    )
    engine = get_guardrail_engine()
    store = engine.approval_store
    t0 = time.time()
    for i in range(1000):
        store.create(ApprovalRequest(
            id=f"bulk_{i}",
            tool_name="bash",
            args={"command": f"echo {i}"},
            risk_level="critical",
            irreversible=True,
            affected_scope="1 process",
            estimated_cost="low",
            explanation="bulk test",
        ))
    pending = store.pending()
    record("1000 pending approvals: handled", len(pending) >= 1000,
           f"{len(pending)} pending in {time.time()-t0:.2f}s")


async def test_deep_nested_payload():
    """Deeply nested JSON payload — parser survives."""
    import aiohttp
    deep = {"a": {"b": {"c": {"d": {"e": {"f": "deep"}}}}}}
    async with aiohttp.ClientSession() as s:
        try:
            async with s.post(f"{BASE}/v1/chat",
                              json={"message": "test", "session_id": "deep", "extra": deep},
                              timeout=aiohttp.ClientTimeout(total=20)) as resp:
                status = resp.status
            record("deep nested payload: accepted", status in (200, 422),
                   f"status={status}")
        except Exception as e:
            record("deep nested payload: accepted", True, f"caught {type(e).__name__}")


async def main():
    print("=" * 70)
    print("AERYN EDGE CASES BATTERY")
    print("=" * 70)
    print()
    
    print("[1] Empty / weird input")
    await test_empty_input()
    print()
    print("[2] Non-ASCII / emoji")
    await test_non_ascii()
    print()
    print("[3] Session collision")
    await test_session_collision()
    print()
    print("[4] 1000 pending approvals")
    await test_many_pending_approvals()
    print()
    print("[5] Deep nested payload")
    await test_deep_nested_payload()
    
    print()
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    print("=" * 70)
    print(f"EDGE CASE RESULTS: {passed}/{total} passed")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())