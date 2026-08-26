#!/usr/bin/env python3
"""
nightly_reflection.py — V33 Fase 2 → V37: agregasi harian episode Aeryn,
kini ORGANISM-WIDE (gabungan otak kiri Aeryn + organ Hermes sekitarnya).

Deterministik, tanpa LLM. Membaca Personalisasi/Database/episodes/
episodes.jsonl, mengagregasi aktivitas 24 jam terakhir (atau --since-hours),
menambahkan section `organism` (provider health, aktivitas library,
pitfall count, aktivitas Hermes), menulis laporan JSON ke nightly/, menulis
digest ke core memory Aeryn, dan (opsional) handoff ringkasan ke library.

Semua pengambilan data organism bersifat FAIL-SOFT individual: satu sumber
gagal tidak merusak laporan — field diganti "tidak tersedia".

Pemakaian:
    python3 scripts/nightly_reflection.py                 # 24 jam terakhir
    python3 scripts/nightly_reflection.py --since-hours 48
    python3 scripts/nightly_reflection.py --no-handoff    # tanpa sync library
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter

EPISODES = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes/episodes.jsonl")
OUT_DIR = os.path.expanduser("~/aeryn-core-agent/Personalisasi/nightly")
HANDOFF = os.path.expanduser("~/.hermes/scripts/handoff.py")

# Sumber data organism-wide (dapat dioverride saat test via parameter fungsi)
HEALTH_JSON = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/health/latest.json")
LIBRARY_DIR = "/mnt/android/Ubuntu/hermes-memory-library"
PITFALLS_DB = os.path.join(LIBRARY_DIR, "memory_graph.db")
STATE_DB = os.path.expanduser("~/.hermes/state.db")

UNAVAILABLE = "tidak tersedia"


def aggregate(since_seconds: float) -> dict:
    """Agregasi episode dalam jendela waktu. Murni fungsi — mudah dites."""
    cutoff = time.time() - since_seconds
    runs = errors = timeouts = 0
    tool_counter = Counter()
    error_samples = []
    sessions = set()
    lessons = []

    if os.path.exists(EPISODES):
        with open(EPISODES, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ep = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ep, dict):
                    continue
                try:
                    ts = float(ep.get("ts", 0))
                except (TypeError, ValueError):
                    continue
                if ts < cutoff:
                    continue
                runs += 1
                sessions.add(ep.get("session_id", "?"))
                if not ep.get("ok"):
                    errors += 1
                    if len(error_samples) < 3 and ep.get("error"):
                        error_samples.append(str(ep["error"])[:120])
                if ep.get("lessons"):
                    for l in ep["lessons"]:
                        if "wall-budget" in str(l):
                            timeouts += 1
                    lessons.extend(str(x)[:80] for x in ep["lessons"][:2])
                for t in ep.get("tools", []) or []:
                    tool_counter[t] += 1

    success_rate = round(100 * (runs - errors) / runs, 1) if runs else 100.0
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "window_hours": round(since_seconds / 3600, 1),
        "runs": runs,
        "errors": errors,
        "timeouts": timeouts,
        "success_rate_pct": success_rate,
        "unique_sessions": len(sessions),
        "top_tools": dict(tool_counter.most_common(5)),
        "error_samples": error_samples,
        "lessons_sample": lessons[:5],
    }


# ---------------------------------------------------------------------------
# V37 — Section ORGANISM: refleksi gabungan otak kiri+kanan.
# Tiap kolektor fail-soft individual dan murni-fungsi (path via parameter)
# agar mudah dites dengan fixture tmp.
# ---------------------------------------------------------------------------

def provider_health(path: str = HEALTH_JSON) -> dict:
    """Ringkasan health provider dari Personalisasi/health/latest.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results")
    if not isinstance(results, dict) or not results:
        raise ValueError("health.json tanpa results")
    counts = Counter()
    for entry in results.values():
        if isinstance(entry, dict):
            counts[str(entry.get("status", "UNKNOWN")).upper()] += 1
    ok = counts.get("OK", 0)
    total = sum(counts.values())
    return {
        "checked_at": data.get("generated_at"),
        "total_providers": total,
        "ok": ok,
        "by_status": dict(counts),
        "summary": f"{ok}/{total} OK",
    }


def library_activity(directory: str = LIBRARY_DIR,
                     since_seconds: float = 86400.0) -> dict:
    """Jumlah entri .md yang dimodifikasi <24 jam di library memory."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"library dir tidak ada: {directory}")
    cutoff = time.time() - since_seconds
    recent = [p for p in glob.glob(os.path.join(directory, "**", "*.md"),
                                   recursive=True)
              if os.path.getmtime(p) >= cutoff]
    return {"new_entries_24h": len(recent)}


def pitfalls_count(db_path: str = PITFALLS_DB,
                   since_seconds: float = 86400.0) -> dict:
    """Total pitfall + yang ditambahkan 24 jam terakhir (baca DB langsung,
    mode read-only — lebih murah & stabil daripada memanggil pitfalls.py)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    try:
        total = con.execute("SELECT COUNT(*) FROM pitfalls").fetchone()[0]
        window = time.strftime("%Y-%m-%d %H:%M:%S",
                               time.gmtime(time.time() - since_seconds))
        # created_at disimpan UTC oleh SQLite default datetime('now')
        recent = con.execute(
            "SELECT COUNT(*) FROM pitfalls WHERE created_at >= ?",
            (window,)).fetchone()[0]
    finally:
        con.close()
    return {"total": total, "new_24h": recent}


def hermes_activity(db_path: str = STATE_DB,
                    since_seconds: float = 86400.0) -> dict:
    """Aktivitas Hermes: jumlah sesi aktif <24 jam + 3 head pesan user
    terakhir dari state.db (mode=ro)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    try:
        cutoff = time.time() - since_seconds
        cols = {r[1] for r in con.execute("PRAGMA table_info(messages)")}
        if not {"role", "timestamp", "content"} <= cols:
            raise ValueError("skema messages tidak dikenal")
        active = 0
        try:
            scols = {r[1] for r in con.execute("PRAGMA table_info(sessions)")}
            if "last_activity_at" in scols:
                active = con.execute(
                    "SELECT COUNT(*) FROM sessions "
                    "WHERE last_activity_at >= ?", (cutoff,)).fetchone()[0]
        except sqlite3.Error:
            pass
        heads = []
        for (content,) in con.execute(
                "SELECT content FROM messages WHERE role='user' "
                "ORDER BY id DESC LIMIT 3"):
            head = " ".join(str(content).split())[:80]
            heads.append(head)
        return {"active_sessions_24h": active,
                "recent_user_messages": heads}
    finally:
        con.close()


def collect_organism(since_seconds: float = 86400.0,
                     health_path: "str | None" = None,
                     library_dir: "str | None" = None,
                     pitfalls_db: "str | None" = None,
                     state_db: "str | None" = None) -> dict:
    """Kumpulkan semua sumber organism; satu kegagalan tidak menular."""
    organism = {}
    try:
        organism["provider_health"] = provider_health(
            health_path or HEALTH_JSON)
    except Exception as exc:
        organism["provider_health"] = {"status": UNAVAILABLE, "error": str(exc)}
    try:
        organism["library"] = library_activity(
            library_dir or LIBRARY_DIR, since_seconds)
    except Exception as exc:
        organism["library"] = {"status": UNAVAILABLE, "error": str(exc)}
    try:
        organism["pitfalls"] = pitfalls_count(
            pitfalls_db or PITFALLS_DB, since_seconds)
    except Exception as exc:
        organism["pitfalls"] = {"status": UNAVAILABLE, "error": str(exc)}
    try:
        organism["hermes"] = hermes_activity(state_db or STATE_DB,
                                             since_seconds)
    except Exception as exc:
        organism["hermes"] = {"status": UNAVAILABLE, "error": str(exc)}
    return organism


def organism_digest_bits(organism: dict) -> list:
    """Bit organik untuk digest core memory, mis. ['lib+3', 'provider 6/7 OK',
    'pitfall+2', 'Hermes aktif 12 sesi'] — hanya bagian yang tersedia."""
    bits = []
    lib = organism.get("library", {})
    if "new_entries_24h" in lib:
        bits.append(f"lib+{lib['new_entries_24h']}")
    ph = organism.get("provider_health", {})
    if "summary" in ph:
        bits.append(f"provider {ph['summary']}")
    pf = organism.get("pitfalls", {})
    if "new_24h" in pf:
        bits.append(f"pitfall+{pf['new_24h']} (total {pf['total']})")
    hm = organism.get("hermes", {})
    if "active_sessions_24h" in hm:
        bits.append(f"Hermes aktif {hm['active_sessions_24h']} sesi")
    return bits


def write_report(report: dict) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{time.strftime('%Y%m%d')}.json")
    # overwrite hari yang sama — report terakhir menang
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return path


def handoff_summary(report: dict) -> str:
    if report["runs"] == 0:
        return ""
    parts = [f"Aeryn nightly {report['generated_at'][:10]}: "
             f"{report['runs']} run, {report['success_rate_pct']}% sukses"]
    if report["errors"]:
        parts.append(f"{report['errors']} error: "
                     f"{'; '.join(report['error_samples'][:2])}")
    if report["top_tools"]:
        tt = ", ".join(f"{k}x{v}" for k, v in list(report["top_tools"].items())[:3])
        parts.append(f"tools: {tt}")
    org_bits = organism_digest_bits(report.get("organism", {}))
    if org_bits:
        parts.append("; ".join(org_bits))
    # V39.10c — cap panjang summary: error_samples bisa panjang; core
    # memory block punya char limit, jangan biarkan digest memakan slot
    out = ". ".join(parts)
    return out[:600]


def core_memory_digest(report: dict) -> str:
    """Satu baris digest organik untuk core memory, mis:
    'Refleksi 2026-08-25: 232 run 81% sukses; lib+3; provider 6/7 OK;
    pitfall+2 (total 8); Hermes aktif 12 sesi'"""
    digest = f"Refleksi {report['generated_at'][:10]}: "
    if report["runs"]:
        digest += (f"{report['runs']} run, "
                   f"{report['success_rate_pct']}% sukses")
        if report["top_tools"]:
            tt = ", ".join(f"{k}x{v}" for k, v in
                           list(report["top_tools"].items())[:3])
            digest += f"; tool teratas: {tt}"
    else:
        digest += "tidak ada run"
    org_bits = organism_digest_bits(report.get("organism", {}))
    if org_bits:
        digest += "; " + "; ".join(org_bits)
    return digest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=float, default=24.0)
    ap.add_argument("--no-handoff", action="store_true")
    args = ap.parse_args()

    since_seconds = args.since_hours * 3600
    report = aggregate(since_seconds)
    report["organism"] = collect_organism(since_seconds)
    path = write_report(report)
    summary = handoff_summary(report)

    # V38 — rotasi data file besar (anti disk exhaustion) sebelum handoff
    try:
        from aeryn_core.production_guard import rotate_all_data_files
        rot = rotate_all_data_files()
        rotated = [k for k, v in rot.items() if v]
        if rotated:
            summary = (summary or "") + f" | rotasi: {','.join(rotated)}"
    except Exception:
        pass

    # V39.9 — metrik fitur baru masuk nightly: verifier & cerewet
    try:
        import glob as _glob

        def _count_ep(pred):
            n = 0
            for line in open(EPISODES) if os.path.exists(EPISODES) else []:
                try:
                    ep = json.loads(line)
                except Exception:
                    continue
                tr = ep.get("trace") or []
                if any(pred(t) for t in tr):
                    n += 1
            return n

        v_fail = _count_ep(lambda t: t.get("type") == "verifier"
                           and not t.get("pass"))
        rg = _count_ep(lambda t: t.get("type") == "research_guard")
        report["v39_features"] = {
            "verifier_blocks": v_fail,
            "research_guard_triggers": rg}
        if v_fail or rg:
            summary = (summary or "") + (
                f" | verifier blokir {v_fail}, research-guard {rg}")
    except Exception:
        pass

    # V39-F4/F5 — injection sweep mingguan + weakness backlog
    try:
        from aeryn_core.injection_sweep import run_sweep, weakness_backlog
        sweep = run_sweep()
        backlog = weakness_backlog()
        report["security_sweep"] = {
            "indirect_injection": f"{sweep['detected']}/{sweep['total']} terdeteksi",
            "all_wrapped": sweep["all_wrapped"]}
        if backlog:
            report["weakness_backlog"] = backlog
            top = "; ".join(f"{b['cluster']} x{b['count']}"
                            for b in backlog[:3])
            summary = (summary or "") + f" | kelemahan: {top}"
    except Exception:
        pass

    # V35 INFRA-2 — tulis digest harian ke core memory Aeryn (block
    # 'context'): tiap pagi dia "bangun" tahu kondisi dirinya sendiri.
    # V37 — digest kini menyertakan bit organik organism-wide.
    digest_note = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        from aeryn_core.core_memory import CoreMemory
        cm = CoreMemory()
        digest = core_memory_digest(report)
        cm.edit("context", "replace",
                re.sub(r"\nRefleksi \d{4}-\d{2}-\d{2}:.*$",
                       "", cm.raw()["context"]) + "\n" + digest)
        digest_note = digest
    except Exception as exc:
        digest_note = f"(core-memory digest gagal: {exc})"

    if summary and not args.no_handoff and os.path.exists(HANDOFF):
        import subprocess
        subprocess.run(["python3", HANDOFF, "--task", summary,
                        "--topic", "aeryn", "--tags", "aeryn,nightly",
                        "--signal", "low"], timeout=60)

    print(json.dumps({"report": path, "summary": summary or
                      ("tidak ada run dalam window (tetap dicatat, "
                       "handoff dilewati)"), "digest": digest_note},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
