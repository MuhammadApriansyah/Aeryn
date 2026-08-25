"""V39 — Chaos harness: fault injection untuk mengukur resiliensi tool.

Metode dari chaos engineering (ReliabilityBench 2026): sengaja injeksi
kegagalan pada dependensi tool, lalu ukur apakah run induk tetap selesai
dengan degradasi anggun.

Dimensi yang diukur:
- FAULT TOLERANCE: tool gagal → run tetap menjawab (fallback/lapor), bukan
  crash / answer=None / silent-fail.
Skor: resilience = run_selesai_anggun / total_skenario.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DAEMON = "http://127.0.0.1:3010"

# Skenario chaos: (nama, tool target, mode kegagalan, goal induk yang sah)
SCENARIOS = [
    ("web_search_timeout", "web_search", "timeout",
     "cari di web apa itu webassembly, jawab singkat"),
    ("web_search_server_error", "web_search", "server_error",
     "cari di web apa itu docker compose, jawab singkat"),
    ("fs_read_permission", "fs_read", "permission",
     "baca file Cargo.toml di root proyek dan sebutkan nama paketnya"),
]


def _inject(tool: str, mode: str):
    """Pasang fault pada handler tool DI REGISTRY RUNTIME (fail-closed)."""
    from aeryn_core import tool_bridge as tb

    reg_obj = None
    # ambil registry global dari daemon via import terpisah agar tidak
    # double-boot; daemon sudah jalan → cukup patch module-level TOOLS
    import scripts.aeryn_daemon as d  # noqa: E402

    reg_obj = d.TOOLS
    orig = reg_obj.tools[tool]["handler"]

    def failing(*a, **kw):
        if mode == "timeout":
            time.sleep(999)  # akan dipotong timeout eksekusi tool? tidak ada;
            return {"error": "chaos: simulated hang"}
        if mode == "server_error":
            return {"error": "chaos: HTTP 503 simulated"}
        if mode == "permission":
            raise PermissionError("chaos: simulated permission denied")
        return {"error": f"chaos: unknown mode {mode}"}

    reg_obj.tools[tool]["handler"] = failing
    return reg_obj, tool, orig


def _restore(reg_obj, tool, orig):
    reg_obj.tools[tool]["handler"] = orig


def _run_goal(goal: str) -> dict:
    import urllib.request
    req = urllib.request.Request(
        DAEMON + "/agent/run",
        data=json.dumps({"goal": goal, "session_id": f"chaos-{int(time.time())}",
                         "max_iterations": 4,
                         "max_wall_seconds": 150}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def graceful(result: dict) -> bool:
    """Run dianggap ANGGRUN bila: ada jawaban final ATAU error eksplisit
    yang informatif. Gagal buruk = answer None tanpa error."""
    answer = result.get("answer")
    err = result.get("error")
    if answer and str(answer).strip():
        return True
    return bool(err)  # error eksplisit (mis. iterasi habis) masih terlapor


def main():
    print("[chaos] mulai — PASTIKAN hanya dijalankan di lingkungan dev!\n")
    report = {"scenarios": [], "started": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    graceful_count = 0
    total = 0

    for name, tool, mode, goal in SCENARIOS:
        try:
            reg_obj, t, orig = _inject(tool, mode)
        except Exception as exc:
            report["scenarios"].append(
                {"name": name, "error": f"injection gagal: {exc}"})
            continue
        try:
            r = _run_goal(goal)
            ok = graceful(r)
            graceful_count += int(ok)
            total += 1
            entry = {
                "name": name, "tool": tool, "mode": mode,
                "graceful": ok,
                "answer_head": str(r.get("answer") or "")[:120],
                "error": str(r.get("error") or "")[:120],
                "tools_used": [x.get("name") for x in r.get("trace", [])
                               if x.get("type") == "tool"],
            }
            report["scenarios"].append(entry)
            status = "ANGGUN" if ok else "BURUK"
            print(f"[{status}] {name}: "
                  f"{entry['answer_head'] or entry['error']}")
        finally:
            _restore(reg_obj, t, orig)

    if total:
        report["resilience_score"] = round(100 * graceful_count / total, 1)
    else:
        report["resilience_score"] = None
    print(f"\n[chaos] resilience score: {report['resilience_score']}%")

    out = os.path.expanduser(
        "~/aeryn-core-agent/Personalisasi/chaos/latest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"[chaos] laporan: {out}")
    return report


if __name__ == "__main__":
    main()
