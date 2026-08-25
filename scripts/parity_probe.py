#!/usr/bin/env python3
"""
parity_probe.py — V34: differential testing Hermes <-> Aeryn.

Setiap tool baru HARUS di-probe dari dua sisi:
  1. DIRECT  — panggilan fungsi murni (layer tool)
  2. DAEMON  — lewat pipeline lengkap agent (governance + shadow + LLM memilih
               tool sendiri)
Divergensi antar lapisan (dan antar-jawaban kedua agen) = bahan perkembangan,
bukan kegagalan: selisih menunjukkan drift wiring, salah klasifikasi, atau
perbedaan interpretasi prompt.

Pemakaian:
    python3 scripts/parity_probe.py                 # jalankan semua probe
    python3 scripts/parity_probe.py --json out.json # simpan report
"""
import argparse
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DAEMON = "http://127.0.0.1:3010"


def _post(path: str, payload: dict, timeout: int = 120):
    req = urllib.request.Request(
        DAEMON + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ── Probe definitions ────────────────────────────────────────────────
def probe_direct_tools():
    """Lapisan 1: fungsi tool langsung — hasil harus deterministik."""
    from aeryn_core.tool_bridge import build_default_registry
    from aeryn_core.hermes_brain import register
    reg = build_default_registry(sandbox_roots=["~/aeryn-core-agent"])
    register(reg)
    out = {}
    r = reg.execute("memory_search", {"query": "webnovel stack framework", "top": 2})
    out["memory_search"] = {
        "ok": isinstance(r, dict) and bool(r.get("results")),
        "expect_hit": any("fastify" in json.dumps(x).lower()
                          for x in r.get("results", []))}
    r = reg.execute("pitfall_search", {"symptom": "SSL EOF"})
    out["pitfall_search"] = {
        "ok": isinstance(r, dict),
        "expect_hit": any(p["id"] == "ddg-blocked-proot"
                          for p in r.get("pitfalls", []))}
    r = reg.execute("graph_traverse", {"entity": "aeryn-core"})
    out["graph_traverse"] = {
        "ok": isinstance(r, dict) and bool(r.get("edges")),
        "expect_hit": any(e["target"] == "aeryn-core-v30-plus"
                          for e in r.get("edges", []))}
    # V35 INFRA-3 — fs_write: roundtrip dalam sandbox + tolak path luar
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        reg2 = build_default_registry(sandbox_roots=[td])
        w = reg2.execute("fs_write", {
            "path": f"{td}/probe/tulis.txt",
            "content": "parity-probe fs_write"})
        reread = reg2.execute("fs_read", {"path": f"{td}/probe/tulis.txt"})
        escape_ok = False
        esc = reg2.execute("fs_write", {
            "path": "/etc/passwd", "content": "harusnya ditolak"})
        # execute() menelan exception → tolakan berupa dict {"error": ..}
        escape_ok = isinstance(esc, dict) and bool(esc.get("error"))
        out["fs_write"] = {
            "ok": (isinstance(w, dict) and w.get("ok") is True
                   and isinstance(reread, dict)
                   and "parity-probe" in str(reread.get("content", ""))
                   and escape_ok),
            "sandbox_escape_blocked": escape_ok}
    return out


def probe_classification():
    """Lapisan 2: kesepakatan dua detektor klasifikasi sosial."""
    from scripts.aeryn_daemon import _is_social_query as d
    from scripts.social_generator import _is_social_query as g
    cases = {
        "halo": True, "kamu agy": True,
        "ingat ini: proyek x": False, "apa itu react": False,
        "catat: sen suka kopi": False, "gimana cara kerja HNSW": False}
    agree, diverge = [], []
    for q, expected in cases.items():
        rd, rg = d(q), g(q)
        entry = {"query": q, "expected": expected, "daemon": rd, "gen": rg}
        if rd == rg == expected:
            agree.append(entry)
        else:
            diverge.append(entry)
    return {"agree": len(agree), "diverge": diverge}


def probe_daemon_e2e():
    """Lapisan 3: pipeline penuh — apakah agent MEMILIH tool yang benar.

    Provider error (HTTP 429/5xx/unreachable) → 'inconclusive', BUKAN
    divergensi: kegagalan LLM bukan salah wiring. Probe boleh diulang.
    """
    out = {}

    def _classify_run(r):
        err = str(r.get("error") or "")
        if any(k in err for k in ("HTTP 429", "HTTP 5", "unreachable",
                                  "semua model fallback habis")):
            return {"ok": None, "inconclusive": err[:120]}
        return None

    r = _post("/agent/run", {"goal": "ingat ini: probe-parity fakta uji",
                             "session_id": "parity-probe", "max_iterations": 3})
    tools = [t.get("name") for t in r.get("trace", []) if t.get("type") == "tool"]
    inc = _classify_run(r)
    out["memory_write_command"] = inc or {
        "tools_chosen": tools,
        "ok": "core_memory_edit" in tools}

    r = _post("/agent/run", {"goal": "halo", "session_id": "parity-probe",
                             "max_iterations": 2})
    tools = [t.get("name") for t in r.get("trace", []) if t.get("type") == "tool"]
    inc = _classify_run(r)
    out["social_no_tool"] = inc or {
        "tools_chosen": tools,
        "answer_head": str(r.get("answer", ""))[:80],
        "ok": tools == []}

    # core memory roundtrip: fakta yang ditulis di atas harus terbaca lagi
    # (hanya valid kalau penulisan tadi sukses, bukan inconclusive)
    cm_path = os.path.expanduser(
        "~/aeryn-core-agent/Personalisasi/Database/core_memory.json")
    try:
        cm = json.load(open(cm_path))
        written = ("probe-parity" in
                   cm.get("context", {}).get("value", "") +
                   cm.get("human", {}).get("value", ""))
        if out["memory_write_command"].get("ok") is not True:
            out["core_memory_roundtrip"] = {"ok": None,
                                            "inconclusive": "penulisan tidak terkonfirmasi"}
        else:
            out["core_memory_roundtrip"] = {"ok": written}
    except Exception as exc:
        out["core_memory_roundtrip"] = {"ok": False, "error": str(exc)[:100]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "direct": {}, "classification": {}, "daemon": {}}

    print("[probe 1/3] direct tool layer...")
    try:
        report["direct"] = probe_direct_tools()
    except Exception as exc:
        report["direct"] = {"error": f"{type(exc).__name__}: {exc}"[:200]}

    print("[probe 2/3] classification agreement...")
    try:
        report["classification"] = probe_classification()
    except Exception as exc:
        report["classification"] = {"error": str(exc)[:200]}

    print("[probe 3/3] daemon end-to-end (butuh daemon hidup)...")
    try:
        report["daemon"] = probe_daemon_e2e()
    except Exception as exc:
        report["daemon"] = {"error": f"{type(exc).__name__}: {exc}"[:200]}

    # verdict ringkas
    issues = []
    inconclusive = []
    for name, r in report["direct"].items():
        if isinstance(r, dict):
            core = {k: v for k, v in r.items()
                    if k not in ("expect_hit", "sandbox_escape_blocked")}
            if not all(core.values()):
                issues.append(f"direct/{name}")
            elif ("expect_hit" in r
                  and not r["expect_hit"] and core.get("ok")):
                issues.append(f"direct/{name}/expect")
    if report["classification"].get("diverge"):
        issues.append(f"classification ({len(report['classification']['diverge'])} diverge)")
    for name, r in report["daemon"].items():
        if not isinstance(r, dict):
            continue
        if r.get("ok") is None:
            inconclusive.append(f"{name}: {r.get('inconclusive', '')[:60]}")
        elif not r.get("ok"):
            issues.append(f"daemon/{name}")

    report["inconclusive"] = inconclusive
    report["issues"] = issues
    if issues:
        report["verdict"] = (f"DIVERGENSI {len(issues)}: " + ", ".join(issues))
    elif inconclusive:
        report["verdict"] = ("INCONCLUSIVE (provider error — ulangi probe): "
                             + "; ".join(inconclusive))
    else:
        report["verdict"] = "ALL PARITY"

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print(f"[report] {args.json_out}")
    print(json.dumps(report["verdict"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
