#!/usr/bin/env python3
"""Phase 6 Evaluation E2E Test."""

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
print("PHASE 6 EVALUATION E2E TEST")
print("=" * 60)

# 1. Metrics endpoint
print("\n[1] Metrics")
r = requests.get(f"{BASE}/v1/eval/metrics")
check("metrics 200", r.status_code == 200)
metrics = r.json()
check("has success_rate", "success_rate" in metrics)
check("has progress_rate", "avg_progress_rate" in metrics)
check("has tool_selection", "avg_tool_selection_accuracy" in metrics)

# 2. Record evaluation
print("\n[2] Record evaluation")
r = requests.post(f"{BASE}/v1/eval/record", json={
    "episode_id": "e2e_eval_1",
    "task": "Explain 2+2",
    "expected_outcome": "4",
    "actual_output": "2+2 equals 4",
    "expected_tools": [],
    "actual_tools": [],
})
check("record 200", r.status_code == 200)
check("auto-scored success", r.json().get("success") == True)

# 3. Benchmarks
print("\n[3] Benchmarks")
r = requests.get(f"{BASE}/v1/eval/benchmarks")
check("benchmarks 200", r.status_code == 200)
check("has scenarios", "scenarios" in r.json())
check("has coverage", "coverage" in r.json())
coverage = r.json().get("coverage", {})
check("tool_use coverage", "tool_use" in coverage)

# 4. Diagnostics
print("\n[4] Diagnostics")
r = requests.post(f"{BASE}/v1/eval/diagnostics/attribute", params={"episode_id": "e2e_eval_1", "trace_id": ""})
check("attribute 200", r.status_code == 200)
check("has culprit_step", "culprit_step" in r.json())

# 5. List episodes
print("\n[5] Episodes")
r = requests.get(f"{BASE}/v1/eval/episodes")
check("episodes 200", r.status_code == 200)

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)