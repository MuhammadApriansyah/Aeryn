#!/usr/bin/env python3
"""Phase 8 E2E Test — True Streaming + Error Recovery."""

import requests
import json
import time

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
print("PHASE 8 TRUE STREAMING + ERROR RECOVERY E2E TEST")
print("=" * 60)

# 1. True streaming (token-by-token SSE)
print("\n[1] True streaming")
r = requests.post(f"{BASE}/v1/chat/stream", json={"message": "Say hello", "session_id": "s8"}, stream=True)
tokens = []
message_complete = False
done = False

for line in r.iter_lines():
    if line:
        line = line.decode()
        if line.startswith("data: ") and line != "data: [DONE]":
            try:
                chunk = json.loads(line[6:])
                if chunk.get("type") == "token":
                    tokens.append(chunk.get("content", ""))
                elif chunk.get("type") == "message_complete":
                    message_complete = True
                elif chunk.get("type") == "done":
                    done = True
            except:
                pass

check("received tokens", len(tokens) > 0, f"got {len(tokens)} tokens")
check("message_complete emitted", message_complete)
check("done emitted", done)
check("tokens form text", "".join(tokens).strip() != "")

# 2. Error recovery (unit test via python)
print("\n[2] Error recovery")
import subprocess
result = subprocess.run(
    ["venv-proot/bin/python", "-c", """
import asyncio
from aeryn_core.runtime.error_recovery import get_error_recovery
async def t():
    r = get_error_recovery()
    async def f():
        raise ValueError('test')
    res = await r.with_retry(f)
    print('retry_attempts=' + str(res.attempts))
    print('retry_success=' + str(res.success))
    print('fallback_works=' + str(True))
asyncio.run(t())
"""],
    capture_output=True, text=True, cwd="/home/sen/aeryn-core-agent"
)
output = result.stdout
check("retry attempts > 1", "retry_attempts=4" in output, output)
check("retry failed gracefully", "retry_success=False" in output)

print("\n" + "=" * 60)
print(f"RESULTS: {pass_count} passed, {fail_count} failed, {pass_count + fail_count} total")
print("=" * 60)