#!/usr/bin/env python3
"""
nightly_reflection.py — V33 Fase 2: agregasi harian episode Aeryn.

Deterministik, tanpa LLM. Membaca Personalisasi/Database/episodes/
episodes.jsonl, mengagregasi aktivitas 24 jam terakhir (atau --since-hours),
menulis laporan JSON ke nightly/, dan (opsional) menyalin ringkasan ke
library Hermes via handoff CLI.

Pemakaian:
    python3 scripts/nightly_reflection.py                 # 24 jam terakhir
    python3 scripts/nightly_reflection.py --since-hours 48
    python3 scripts/nightly_reflection.py --no-handoff    # tanpa sync library
"""
import argparse
import json
import os
import re
import sys
import time
from collections import Counter

EPISODES = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes/episodes.jsonl")
OUT_DIR = os.path.expanduser("~/aeryn-core-agent/Personalisasi/nightly")
HANDOFF = os.path.expanduser("~/.hermes/scripts/handoff.py")


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
    return ". ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=float, default=24.0)
    ap.add_argument("--no-handoff", action="store_true")
    args = ap.parse_args()

    report = aggregate(args.since_hours * 3600)
    path = write_report(report)
    summary = handoff_summary(report)

    # V35 INFRA-2 — tulis digest harian ke core memory Aeryn (block
    # 'context'): tiap pagi dia "bangun" tahu kondisi dirinya sendiri.
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        from aeryn_core.core_memory import CoreMemory
        cm = CoreMemory()
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
        cm.edit("context", "replace",
                re.sub(r"\nRefleksi \d{4}-\d{2}-\d{2}:.*$", "",
                       cm.raw()["context"]) + "\n" + digest)
    except Exception as exc:
        summary_note = f"(core-memory digest gagal: {exc})"

    if summary and not args.no_handoff and os.path.exists(HANDOFF):
        import subprocess
        subprocess.run(["python3", HANDOFF, "--task", summary,
                        "--topic", "aeryn", "--tags", "aeryn,nightly",
                        "--signal", "low"], timeout=60)

    print(json.dumps({"report": path, "summary": summary or
                      ("tidak ada run dalam window (tetap dicatat, "
                       "handoff dilewati)")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
