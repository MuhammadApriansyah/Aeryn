#!/usr/bin/env python3
"""Phase 7 Multi-Agent Orchestration E2E Test."""

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
print("PHASE 7 MULTI-AGENT ORCHESTRATION E2E TEST")
print("=" * 60)

# 1. Routing
print("\n[1] Supervisor routing")
r = requests.post(f"{BASE}/v1/orchestrate/route", params={"task": "Write a poem"})
check("route creative", r.status_code == 200 and r.json().get("division") == "creative")
r = requests.post(f"{BASE}/v1/orchestrate/route", params={"task": "Deploy server"})
check("route infra", r.json().get("division") == "infra")

# 2. Handoff
print("\n[2] Handoff")
r = requests.post(f"{BASE}/v1/orchestrate/handoff", json={
    "from_division": "creative", "to_division": "reasoning", "task": "Critique poem"
})
check("handoff 200", r.status_code == 200)
check("handoff from/to", r.json().get("from_agent") == "creative" and r.json().get("to_agent") == "reasoning")

# 3. Broadcast
print("\n[3] Broadcast")
r = requests.post(f"{BASE}/v1/orchestrate/broadcast", params={"sender": "supervisor", "message": "Hello all"})
check("broadcast 200", r.status_code == 200)
check("broadcast to 5 divisions", len(r.json().get("recipients", [])) == 5)

# 4. Blackboard
print("\n[4] Blackboard")
r = requests.get(f"{BASE}/v1/orchestrate/blackboard")
check("blackboard 200", r.status_code == 200)

# 5. Metrics
print("\n[5] Coordination metrics")
r = requests.get(f"{BASE}/v1/orchestrate/metrics")
check("metrics 200", r.status_code == 200)
check("has communication_count", "communication_count" in r.json())
check("has coordination_efficiency", "coordination_efficiency" in r.json())

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)