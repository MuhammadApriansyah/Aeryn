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

# V36 — TTL cache ringkasan LLM (detik): 6 jam.
COMPACT_TTL = 6 * 3600

# Batas panjang teks turn lama yang dikirim ke llm_summarize (karakter).
_COMPACT_INPUT_MAX = 4000


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


def _compact_path(sid):
    """Path file cache ringkasan LLM per-sesi (<sid>.compact.json)."""
    import re
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sid)
    safe = re.sub(r"\.{2,}", "_", safe)  # tanpa traversal ".."
    return os.path.join(_DB_DIR, f"{safe}.compact.json")


def _read_compact_cache(cp, now=None):
    """Baca cache ringkasan LLM. Return str kalau valid & belum kadaluarsa,
    selain itu None (tidak ada / korup / kadaluarsa)."""
    if now is None:
        now = time.time()
    try:
        with open(cp) as f:
            c = json.load(f)
        ts = float(c.get("ts", 0))
        summary = c.get("summary")
        if isinstance(summary, str) and summary.strip() \
                and (now - ts) < COMPACT_TTL:
            return summary
    except (OSError, ValueError, TypeError, AttributeError):
        pass  # cache hilang/korup → anggap tidak ada
    return None


def _llm_summary_cached(sid, old_turns, llm_summarize):
    """Ringkasan LLM turn lama dengan cache per-sesi TTL 6 jam.

    - Cache valid → pakai tanpa menelepon LLM.
    - Cache kadaluarsa/tidak ada → gabung teks turn lama (maks
      _COMPACT_INPUT_MAX char), panggil llm_summarize, tulis cache.
    - Return None kalau llm_summarize gagal (exception apapun) atau
      hasilnya bukan string non-kosong → pemanggil fallback ke
      _summarize_old. Tidak pernah raise; kegagalan tidak di-cache.
    """
    cp = _compact_path(sid)
    now = time.time()
    cached = _read_compact_cache(cp, now=now)
    if cached is not None:
        return cached
    # Susun teks mentah turn lama, potong sebelum dikirim ke LLM.
    text = "\n".join(f'{t["role"]}: {t["content"]}' for t in old_turns)
    text = text[:_COMPACT_INPUT_MAX]
    try:
        summary = llm_summarize(text)
    except Exception:
        return None  # LLM gagal → fallback deterministik di pemanggil
    if not isinstance(summary, str) or not summary.strip():
        return None
    try:
        os.makedirs(_DB_DIR, exist_ok=True)
        with open(cp, "w") as f:
            json.dump({"ts": round(now, 3), "summary": summary},
                      f, ensure_ascii=False)
    except OSError:
        pass  # gagal menulis cache → tetap kembalikan ringkasan kali ini
    return summary


def load_with_compaction(sid, char_budget=DEFAULT_CHAR_BUDGET,
                         llm_summarize=None):
    """Muat riwayat sesi dengan kompaksi LLM opsional.

    Perilaku sama seperti load(), tapi kalau ada turn lama yang harus
    diringkas dan `llm_summarize` (callable text -> str, DIINJEKSI dari
    luar — biasanya pembungkus ModelClient.chat) tersedia, ringkasan
    dibuat oleh LLM dan di-cache ke <sid>.compact.json (TTL 6 jam)
    supaya LLM tidak ditelepon tiap run. Kalau llm_summarize None atau
    gagal → jatuh kembali ke ringkasan deterministik _summarize_old.
    Tidak pernah raise.
    """
    turns = _load_turns(sid)
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
        old = turns[:remainder]
        summary = None
        if llm_summarize is not None:
            summary = _llm_summary_cached(sid, old, llm_summarize)
        if summary is None:  # fallback: ringkasan deterministik
            summary = _summarize_old(old)
        out.append({"role": "system",
                    "content": f"Riwayat awal sesi:\n{summary}"})
    out += kept
    return out


def _load_turns(sid):
    """Baca & bersihkan turn sesi dari JSONL (dipakai load & compaction).

    Return list dict turn valid; file tidak ada → list kosong.
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
    return [t for t in turns
            if isinstance(t, dict) and t.get("role") and "content" in t]


def load(sid, char_budget=DEFAULT_CHAR_BUDGET):
    """Muat riwayat sesi dalam budget karakter.

    Returns list pesan OpenAI-style. Turn terbaru utuh; sisanya ringkasan.
    """
    turns = _load_turns(sid)
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
