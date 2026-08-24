#!/usr/bin/env python3
"""V29.3 — mentor CLI: panel ringan untuk memantau Aeryn-Core.

Panggilan: ./venv-proot/bin/python scripts/mentor.py [--watch]

Menampilkan:
- success rate (refleksi)
- strategi aktif (GOAL_SAM, < 48h)
- rekomendasi terbaru
- tool graduation status

Butuh daemon Aeryn jalan di 127.0.0.1:3010.
"""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:3010"


def fetch():
    try:
        with urllib.request.urlopen(f"{BASE}/mentor", timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)[:80]}


def render(d):
    if "error" in d:
        print(f"⚠️  daemon unreachable: {d['error']}")
        return
    print(f"📊 Success rate: {d.get('success_rate')} | runs: {d.get('runs')}")
    strats = d.get("active_strategies", [])
    if strats:
        print("\n🧠 Strategi aktif:")
        for s in strats:
            ts = time.strftime("%H:%M:%S", time.localtime(s.get("ts", 0)))
            print(f"  [{ts}] {s['goal'][:50]}")
            # unwrap strategy, print singkat
            strat = s["strategy"].split(":", 1)[-1].strip()
            print(f"    → {strat[:120]}")
    else:
        print("\n✅ Tidak ada strategi pending (semua run cukup).")
    recs = d.get("recommendations", [])
    if recs:
        print("\n💡 Rekomendasi:")
        for text, count in recs:
            print(f"  • {text} (×{count})")
    tools = d.get("tool_status", {})
    if tools:
        print("\n🔧 Tools:")
        for name, t in sorted(tools.items()):
            total = t["success"] + t["fail"]
            rate = f"{t['success']}/{total}" if total else "-"
            print(f"  {name:14s} [{t['status']:10s}] {rate}")


def main():
    watch = "--watch" in sys.argv
    while True:
        d = fetch()
        print("\033[2J\033[H", end="")
        render(d)
        print(f"\n{'━'*40}  {time.strftime('%H:%M:%S')}  (Ctrl+C exit)")
        if not watch:
            break
        time.sleep(8)


if __name__ == "__main__":
    main()
