"""V35 INFRA-1 — SessionHistory: riwayat multi-turn dengan budget & compaction.

Gap terbesar V34: daemon membangun messages=[system, goal] fresh setiap run
→ amnesia antar-pesan di Discord. Modul ini menyimpan riwayat per-sesi dan
mengembalikannya dalam budget karakter:

- Turn TERBARU dipertahankan utuh (paling relevan).
- Turn lama melewati budget diringkas jadi blok "[ringkasan]" deterministik
  (bukan LLM — murah, cepat, tanpa kuota).
- Persist JSONL per sesi di Personalisasi/Database/sessions/.
"""

import json
import os
import threading
import time

_DB_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/sessions")
_LOCK = threading.Lock()

# Budget default injeksi riwayat ke prompt (karakter).
DEFAULT_CHAR_BUDGET = 6000


def _path(sid):
    import re
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sid)
    safe = re.sub(r"\.{2,}", "_", safe)  # tanpa traversal ".."
    return os.path.join(_DB_DIR, f"{safe}.jsonl")


def record(sid, role, content):
    """Simpan satu turn (role: 'user'/'assistant')."""
    os.makedirs(_DB_DIR, exist_ok=True)
    entry = {"ts": round(time.time(), 3), "role": role,
             "content": str(content)[:8000]}
    with _LOCK:
        with open(_path(sid), "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def reset(sid):
    p = _path(sid)
    if os.path.exists(p):
        os.remove(p)


def turn_count(sid):
    try:
        with open(_path(sid)) as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _summarize_old(turns):
    """Ringkasan deterministik turn lama — tanpa LLM."""
    users = [t["content"][:120] for t in turns if t["role"] == "user"]
    n_asst = sum(1 for t in turns if t["role"] == "assistant")
    lines = [f"[ringkasan {len(turns)} turn awal sesi: {n_asst} jawaban]"]
    lines += [f"- tanya: {u}" for u in users[-6:]]
    return "\n".join(lines)


def load(sid, char_budget=DEFAULT_CHAR_BUDGET):
    """Muat riwayat sesi dalam budget karakter.

    Returns list pesan OpenAI-style. Turn terbaru utuh; sisanya ringkasan.
    """
    try:
        with open(_path(sid)) as f:
            turns = []
            for l in f:
                try:
                    t = json.loads(l)
                except ValueError:
                    continue  # baris korup → skip, jangan crash
                turns.append(t)
    except OSError:
        return []
    # buang turn korup/non-dict (lesson hot_pruner/nightly)
    turns = [t for t in turns
             if isinstance(t, dict) and t.get("role") and "content" in t]
    # iterasi dari belakang: kumpulkan turn utuh sampai budget habis
    kept, used = [], 0
    for t in reversed(turns):
        cost = len(t["content"]) + 16
        if used + cost > char_budget:
            break
        kept.append({"role": t["role"], "content": t["content"]})
        used += cost
    kept.reverse()
    remainder = len(turns) - len(kept)
    out = []
    if remainder > 0:
        summary = _summarize_old(turns[:remainder])
        out.append({"role": "system",
                    "content": f"Riwayat awal sesi:\n{summary}"})
    out += kept
    return out
