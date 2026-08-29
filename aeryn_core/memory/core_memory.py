"""V34-1 — CoreMemory: blok memori inti ala Letta/MemGPT.

Context window = RAM analogy: blok teks berlabel yang SELALU di-inject ke
system prompt setiap run, dengan char-limit eksplisit. Agent mengelola isi
blok sendiri via tool `core_memory_edit` (replace/append) — fakta penting
tentang user & proyek bertahan lintas sesi tanpa perlu recall.

Persist: JSON di Personalisasi/Database/core_memory.json.
Blok: "human" (siapa user, gaya komunikasi), "context" (proyek & sistem).
"""
import json
import os
import time

from aeryn_core.utils.config import DATABASE_DIR
DB_DIR = DATABASE_DIR
DEFAULT_PATH = os.path.join(DB_DIR, "core_memory.json")

BLOCK_LIMITS = {"human": 2000, "context": 2000}

_SEED = {
    "human": (
        "Nama: Sen. Bahasa: Indonesia kasual, jawaban singkat & langsung.\n"
        "Relasi: majikan/pembuat — beri wewenang penuh, suka eksekusi "
        "tanpa banyak tanya."),
    "context": (
        "Proyek aktif: aeryn-core-agent (otak kognitif ini, port 3010, PM2 "
        "'aeryn-core'), webnovel-platform (Fastify+React, sesi lain yang "
        "pegang), Hermes agent (infra rumah: gateway WA/Discord, cron, "
        "library memori di /mnt/android).\n"
        "Aeryn bagian dari keluarga sistem Sen — satu otak kolektif lewat "
        "hermes_brain tools."),
}


class CoreMemory:
    def __init__(self, path: str = None):
        self.path = path or DEFAULT_PATH
        self._data = None
        self._mtime = -1

    # ---- persistence ---------------------------------------------------
    def _load(self):
        try:
            m = os.path.getmtime(self.path)
        except OSError:
            self._data = None
            return
        if m == self._mtime and self._data is not None:
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                self._data = json.load(f)
            self._mtime = m
        except (OSError, ValueError):
            self._data = None

    def _ensure(self):
        """Muat atau seed awal (sekali saja — file sudah ada tidak disentuh)."""
        self._load()
        if self._data is not None:
            return
        self._data = {b: {"value": _SEED.get(b, ""), "updated": time.time()}
                      for b in BLOCK_LIMITS}
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=1)

    # ---- operations ------------------------------------------------------
    def edit(self, block: str, mode: str, content: str) -> dict:
        """Edit blok. mode: 'replace' (timpa) / 'append' (sambung).

        Char-limit ditindaklanjuti: kalau melampaui limit, teks terlama
        dipangkas dari depan (append) atau dipotong (replace).
        V38.4 — audit log append-only: setiap edit tercatat ke
        <path>.audit.jsonl (ts, block, mode, chars, head) — memori inti
        adalah aspek identitas; perubahan harus bisa ditelusuri.
        """
        self._ensure()
        if self._data is None:  # pragma: no cover — _ensure selalu set
            self._data = {b: {"value": "", "updated": 0.0} for b in BLOCK_LIMITS}
        if block not in BLOCK_LIMITS:
            return {"ok": False,
                    "error": f"block harus salah satu dari {list(BLOCK_LIMITS)}"}
        if mode not in ("replace", "append"):
            return {"ok": False, "error": "mode harus replace|append"}
        content = (content or "").strip()
        if not content:
            return {"ok": False, "error": "content kosong"}

        limit = BLOCK_LIMITS[block]
        cur = self._data[block]["value"]
        if mode == "replace":
            new_val = content[:limit]
        else:
            new_val = (cur + "\n" + content)[-limit:]
        self._data[block] = {"value": new_val, "updated": time.time()}
        self._save()
        # V38.4 — audit trail append-only (gagal tulis log ≠ gagal edit)
        try:
            with open(self.path + ".audit.jsonl", "a", encoding="utf-8") as af:
                af.write(json.dumps({
                    "ts": round(time.time(), 3), "block": block,
                    "mode": mode, "chars": len(content),
                    "head": content[:80]}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return {"ok": True, "block": block, "chars": len(new_val),
                "limit": limit}

    def render(self) -> str:
        """Blok prompt untuk system-prompt injection (selalu dipanggil)."""
        self._ensure()
        lines = ["\n## Memori inti (fakta tetap — kamu kelola sendiri)"]
        for block, label in (("human", "Tentang user"),
                             ("context", "Konteks proyek/sistem")):
            val = self._data[block]["value"].strip()
            n = len(val)
            lines.append(f"<{block} chars={n}/{BLOCK_LIMITS[block]}>")
            lines.append(val if val else "(kosong)")
            lines.append(f"</{block}>")
        lines.append(
            "Ini memori MILIKMU. Gunakan tool `core_memory_edit` untuk "
            "memperbarui saat ada fakta baru penting. Jangan dibacakan "
            "ke user — pakai secara alami.")
        return "\n".join(lines)

    def raw(self) -> dict:
        """Isi mentah (untuk /metrics atau debug)."""
        self._ensure()
        return {b: self._data[b]["value"] for b in BLOCK_LIMITS}
