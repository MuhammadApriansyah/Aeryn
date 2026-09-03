#!/usr/bin/env python3
"""Phase 5 E2E Test — Production Hardening (guardrails, runtime, observability, session, auth)."""

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
print("PHASE 5 PRODUCTION HARDENING E2E TEST")
print("=" * 60)

# 5.1 Guardrails
print("\n[5.1] Guardrails + HITL")
r = requests.get(f"{BASE}/v1/approvals/policies")
check("policies 200", r.status_code == 200)
check("bash requires approval", r.json().get("policies", {}).get("bash", {}).get("requires_approval") == True)

# 5.2 Runtime
print("\n[5.2] Execution Runtime")
r = requests.post(f"{BASE}/v1/tasks/submit", json={"type": "echo", "payload": {"msg": "test"}})
check("submit returns task_id", r.status_code == 200 and "task_id" in r.json())
r = requests.get(f"{BASE}/v1/tasks/")
check("list tasks 200", r.status_code == 200)

# 5.3 Observability
print("\n[5.3] Observability")
r = requests.get(f"{BASE}/v1/traces/")
check("traces 200", r.status_code == 200)

# 5.4 Session State
print("\n[5.4] Session State")
r = requests.get(f"{BASE}/v1/sessions", params={"user_id": "e2e_user"})
check("sessions 200 (user-scoped)", r.status_code == 200)

# 5.5 Auth
print("\n[5.5] Identity + Auth")
r = requests.post(f"{BASE}/v1/auth/issue-key", json={"user_id": "e2e_user", "allowed_tools": ["file_read"]})
check("issue-key 200", r.status_code == 200)
api_key = r.json().get("api_key", "")
r = requests.post(f"{BASE}/v1/auth/validate", params={"api_key": api_key})
check("validate key", r.status_code == 200 and r.json().get("valid") == True)
r = requests.get(f"{BASE}/v1/auth/tool-permission", params={"tool_name": "bash", "user_id": "e2e_user"})
check("bash forbidden for restricted user", r.json().get("allowed") == False)

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)