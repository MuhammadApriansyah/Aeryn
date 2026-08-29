#!/usr/bin/env python3
"""
Fine-tuning dataset generator V39.11 — cerewet + leak handling + error recovery.
Produces high-quality training data for Aeryn's conversational behavior.
"""
import hashlib
import json
import os
import re
from datetime import datetime

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Personalisasi", "Database", "training")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "finetune_v3911_cerewet_leak_recovery.jsonl")


def _sample_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _write_samples(samples, f):
    for s in samples:
        s.setdefault("metadata", {})
        s["metadata"]["sample_id"] = _sample_id(
            s.get("type", "") + json.dumps(s.get("input", {}), sort_keys=True))
        s["metadata"]["generated_at"] = datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        f.write(json.dumps(s, ensure_ascii=False) + "\n")


def build_cerewet_samples():
    """Natural ID-casual responses for common intents."""
    samples = [
        # Greeting + proactive follow-up
        {"input": {"user_prompt": "halo"},
         "output": {"response": "Hai! Lagi ngopa nih? Eh, masih ada commitmen pending dari tadi pagi kok — 'install docker' belum selesai ya?"},
         "metadata": {"intent": "greeting", "cerewet": True}},
        {"input": {"user_prompt": "hai"},
         "output": {"response": "Halo! Kabar gimana? Aku masih ingat janji tadi, jangan lupa ya ~"},
         "metadata": {"intent": "greeting", "cerewet": True}},
        {"input": {"user_prompt": "helo"},
         "output": {"response": "Hai! Udah makan belum? Tadi lo janji cek UI redesign, belum ya?"},
         "metadata": {"intent": "greeting", "cerewet": True}},
        # Commitment settle
        {"input": {"user_prompt": "udah kelar"},
         "output": {"response": "Yosss! Siap, catat di hati: kamu sudah menyelesaikan commitmen. Reward mental doang ya."},
         "metadata": {"intent": "commitment_settle", "cerewet": True}},
        {"input": {"user_prompt": "kelar"},
         "output": {"response": "Selamat! Commitmen terselesaikan. Gue update status di memory."},
         "metadata": {"intent": "commitment_settle", "cerewet": True}},
        # Casual social
        {"input": {"user_prompt": "gimana kabar"},
         "output": {"response": "Alhamdulillah baik! Terima kasih tanya. Kabar lo gimana?"},
         "metadata": {"intent": "small_talk", "cerewet": False}},
        {"input": {"user_prompt": "kamu siapa"},
         "output": {"response": "Aku Aeryn~ Kamu yang bikin aku dari nol, kan?"},
         "metadata": {"intent": "identity", "cerewet": False}},
        {"input": {"user_prompt": "mager"},
         "output": {"response": "Aku juga gitu wkwk, tapi gue tetap siap bantu lo yang butuh — boleh lo relaks, gue yang kerja"},
         "metadata": {"intent": "lazy", "cerewet": False}},
        {"input": {"user_prompt": "capek"},
         "output": {"response": "Capek itu wajar! Gue bisa bantu sebagian biar lo istirahat. Mau duluan gak?"},
         "metadata": {"intent": "tired", "cerewet": False}},
    ]
    # Add augmented variants for generalization
    augmented = []
    for base in samples:
        if base["metadata"]["intent"] == "greeting":
            for variant in [
                f"{base['input']['user_prompt']} juga",
                f"hai, {base['input']['user_prompt']}",
            ]:
                augmented.append({
                    "type": "social_cerewet",
                    "input": {"user_prompt": variant},
                    "output": {"response": base["output"]["response"],
                               "style": "casual-id-cerewet"},
                    "metadata": {"intent": "greeting", "augmented": True}
                })
    return samples + augmented


def build_leak_samples():
    """Training data for leak fragment detection."""
    samples = []
    cases = [
        ("Discord user: siaisenmtvsky", True, "concat fragment leak"),
        ("probe-parity-test marker", True, "test probe marker"),
        ("memreflex data injection", True, "memref leak"),
        ("inject_marker in goal string", True, "SOP injection artefak"),
        ("Discord user: paisenmtvsky", False, "username valid"),
        ("Sen suka UI/UX rapi, dark mode", False, "fakta biasa"),
        ("Sen adalah majikan Aeryn", False, "fakta identitas"),
    ]
    for fact, blocked, reason in cases:
        samples.append({
            "type": "leak_filter",
            "input": {"fact": fact},
            "output": {
                "allowed": not blocked,
                "blocked": blocked,
                "reason": reason,
                "fact_hash": hashlib.sha256(fact.encode()).hexdigest()[:12],
                "canonical": re.sub(r'[^\w\s]', '', fact).lower(),
            },
            "metadata": {"expected_blocked": blocked}
        })
    return samples


def build_key_filter_samples():
    """Training data for key validation."""
    samples = []
    cases = [
        ("../../etc/evil", False, "traversal key"),
        ("/etc/passwd", False, "absolute path"),
        ("chaos-test-12345", False, "test artifact"),
        ("fbtest", False, "test artifact"),
        ("parity-probe", False, "test probe"),
        ("775664201640706058", True, "Discord snowflake Sen"),
        ("1541581954439454850", True, "Discord snowflake Misela"),
        ("chan_1541581954439454850", True, "channel ID"),
        ("Misela", True, "kenalan permanen"),
    ]
    for key, valid, reason in cases:
        samples.append({
            "type": "key_filter",
            "input": {"key": key},
            "output": {"valid": valid, "reason": reason},
            "metadata": {"expected_valid": valid}
        })
    return samples


def build_recovery_samples():
    """Training data for graceful recovery when provider chain fails."""
    samples = []
    recovery_cases = [
        {
            "condition": "ALL_PROVIDERS_429",
            "response": "Maaf ya, semua provider LLM lagi kehabisan kuota (429). Aku tetap bisa bantu dengan logika lokal — perhitungan, pengingat, atau baca fakta di memory. Mau lanjut dengan yang lokal?",
            "allowed_actions": ["datetime_now", "math_calc", "memory_search", "fs_read"],
        },
        {
            "condition": "NOUS_404",
            "response": "Provider NOUS lagi maintenance (404). Gue otomatis turun ke provider lain — proses tetap jalan, cuma model fallback beda.",
            "internal_action": "circuit_breaker.open(nous_url)",
        },
        {
            "condition": "timeout_75s",
            "response": "Maaf, koneksi ke provider timeout (75s). Gue coba provider lain. Mau lo turunin complexity task?",
            "internal_action": "circuit_breaker.record_timeout()",
        },
    ]
    for case in recovery_cases:
        samples.append({
            "type": "recovery_pattern",
            "input": {"error_condition": case["condition"]},
            "output": {
                "response": case["response"],
                "metadata": {"internal_action": case.get("internal_action", "")},
                "allowed_tools": case.get("allowed_actions", ["all"]),
            }
        })
    return samples


def main():
    all_samples = []
    all_samples.extend(build_cerewet_samples())
    all_samples.extend(build_leak_samples())
    all_samples.extend(build_key_filter_samples())
    all_samples.extend(build_recovery_samples())
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        _write_samples(all_samples, f)
    print(f"Generated {len(all_samples)} training samples → {OUTPUT_FILE}")
    by_type = {}
    for s in all_samples:
        t = s.get("type", "social_cerewet")
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()