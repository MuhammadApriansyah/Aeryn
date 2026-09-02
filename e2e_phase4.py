#!/usr/bin/env python3
"""Phase 4 E2E Test — divisions, plugins, planning, reflection."""

import requests
import json

BASE = "http://127.0.0.1:3010"
pass_count = 0
fail_count = 0

def test(name, method, endpoint, expect=200, data=None, params=None):
    global pass_count, fail_count
    url = f"{BASE}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=15)
        else:
            r = requests.post(url, json=data, params=params, timeout=15)
        
        if r.status_code == expect:
            pass_count += 1
            print(f"  ✅ {name}")
        else:
            fail_count += 1
            try:
                print(f"  ❌ {name}: {r.status_code} — {r.json()}")
            except:
                print(f"  ❌ {name}: {r.status_code}")
    except Exception as e:
        fail_count += 1
        print(f"  ❌ {name}: {e}")

print("=" * 60)
print("PHASE 4 E2E TEST")
print("=" * 60)

# 1. Divisions
print("\n[1] Divisions")
test("List divisions", "GET", "/v1/divisions")
test("Classify creative", "POST", "/v1/divisions/classify", params={"message": "Write a poem"})
test("Classify psych", "POST", "/v1/divisions/classify", params={"message": "I feel anxious"})
test("Classify reasoning", "POST", "/v1/divisions/classify", params={"message": "Analyze this logic"})
test("Classify gov", "POST", "/v1/divisions/classify", params={"message": "Check requirements"})
test("Classify infra", "POST", "/v1/divisions/classify", params={"message": "Deploy to server"})

# 2. Plugins
print("\n[2] Plugins")
test("Discover plugins", "GET", "/v1/plugins/discover")
test("Load plugins", "POST", "/v1/plugins/load")
test("Plugins list", "GET", "/v1/plugins")

# 3. Planning
print("\n[3] Planning")
test("Decompose goal", "POST", "/v1/plan/decompose", params={"goal": "Build a website"})
test("Make plan", "POST", "/v1/plan", data={"goal": "Test goal"})
test("Get plan", "GET", "/v1/plan/1")

# 4. Reflection
print("\n[4] Reflection")
test("Reflect", "POST", "/v1/reflect", data={"goal": "test", "outcome": "success", "strategy": "incremental"})
test("Recent reflections", "GET", "/v1/reflect/recent")

# 5. Proactive
print("\n[5] Proactive")
test("Record action", "POST", "/v1/proactive/record", data={"action": "search web"})
test("Suggest actions", "GET", "/v1/proactive/suggest")

# 6. Agent (division-integrated)
print("\n[6] Agent with division routing")
test("Agent chat", "POST", "/v1/chat", data={"message": "Hello", "session_id": "phase4_test"})

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)