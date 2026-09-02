#!/usr/bin/env python3
"""Phase 5.1 Guardrail E2E Test — 4-layer guardrail + HITL."""

import requests
import json

BASE = "http://127.0.0.1:3010"
pass_count = 0
fail_count = 0

def check(name, condition, detail=""):
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"  ✅ {name}")
    else:
        fail_count += 1
        print(f"  ❌ {name}: {detail}")

print("=" * 60)
print("PHASE 5.1 GUARDRAIL E2E TEST")
print("=" * 60)

# 1. Policies endpoint
print("\n[1] Policies")
r = requests.get(f"{BASE}/v1/approvals/policies")
check("policies returns 200", r.status_code == 200)
policies = r.json().get("policies", {})
check("bash requires approval", policies.get("bash", {}).get("requires_approval") == True)
check("file_read does NOT require approval", policies.get("file_read", {}).get("requires_approval") == False)

# 2. Agent triggers approval for bash
print("\n[2] Agent triggers HITL approval for bash")
r = requests.post(f"{BASE}/v1/chat", json={"message": "Run: echo test", "session_id": "g_test"})
body = r.json()
check("chat returns 200", r.status_code == 200)
check("response has requires_approval", body.get("requires_approval") == True)
check("approval payload present", "approval" in body)
check("approval has tool_name", body.get("approval", {}).get("tool_name") == "bash")
check("approval has args", "command" in body.get("approval", {}).get("args", {}))

# 3. Pending approvals list
print("\n[3] Pending approvals")
r = requests.get(f"{BASE}/v1/approvals/pending")
check("pending returns 200", r.status_code == 200)
check("pending has count", "count" in r.json())

# 4. Approve flow
print("\n[4] Approve/reject flow")
r = requests.get(f"{BASE}/v1/approvals/pending")
pending = r.json().get("pending", [])
if pending:
    approval_id = pending[0]["id"]
    # Reject test
    r = requests.post(f"{BASE}/v1/approvals/decide", json={"approval_id": approval_id, "decision": "reject"})
    check("reject returns 200", r.status_code == 200)
    check("reject status", r.json().get("status") == "rejected")
else:
    check("pending has items", False, "no pending approvals to test")

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)