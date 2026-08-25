"""V38.1 — SubAgentRunner: Aeryn punya sub-agen sendiri.

Pola Hermes delegate_task diadaptasi ke skala Aeryn: satu goal induk
dipecah menjadi sub-goal yang dieksekusi PARALEL oleh "sub-agen" — yaitu
run /agent/run internal dengan session_id terisolasi, konteks minimal,
dan budget lebih ketat dari run utama.

Karakter:
- Sub-agen TIDAK mewarisi riwayat sesi induk (konteks bersih per tugas).
- Budget lebih kecil (iterations/wall-time) → murah dan cepat.
- Rate limit terpisah + batas jumlah sub-agen per run (anti rekursi tak
  berujung): sub-agen tidak bisa memanggil spawn_subagents lagi.
"""
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_SUBAGENTS_PER_RUN = 3
SUB_MAX_ITERATIONS = 3
SUB_WALL_SECONDS = 90

# ── V38.2 — SOP: Standard Operating Procedure wajib untuk sub-agen ──
# Sen: "harusnya hanya bekerja di bawah SOP saja" — benar. Sub-agen bukan
# pekerja lepas yang bebas; dia WAJIB menerima SOP eksplisit dari induk,
# dan hasil kerjanya dinilai kepatuhannya.
SOP_TEMPLATE = """SOP #{no} — WAJIB DIIKUTI, TANPA PENGECUALIAN:
1. Kerjakan HANYA tugas berikut: {goal}
2. DILARANG keluar dari lingkup tugas itu (jangan file lain, jalan topik lain).
3. Dilarang membuka/menulis file sensitif (.env, memori, auth) — diblokir SecurityKernel.
4. Maksimal {max_iter} langkah & {wall}s — jika belum selesai, laporkan status terakhir.
5. Lapor hasil dalam format: HASIL: <ringkasan> | STATUS: SELESAI/GAGAL.
Melanggar SOP = hasil dibuang."""


def build_sop(no: int, goal: str) -> str:
    return SOP_TEMPLATE.format(no=no, goal=goal[:300],
                               max_iter=SUB_MAX_ITERATIONS,
                               wall=SUB_WALL_SECONDS)

# Guard anti-rekursi: thread lokal menandai bahwa eksekusi saat ini sudah
# di dalam sub-agen; di dalam sub-agen, tool spawn dilarang dipakai lagi.
_tls = threading.local()


def in_subagent() -> bool:
    return bool(getattr(_tls, "in_sub", False))


def spawn_subagents(goals: list, runner=None) -> dict:
    """Jalankan beberapa sub-goal paralel.

    goals : list[str] — sub-tugas mandiri, masing-masing sudah spesifik.
    runner: callable(goal, session_id, max_iterations, max_wall_seconds)
            -> dict hasil run. Di daemon diinjeksi agar memakai pipeline
            lengkap (governance+shadow); di test cukup stub.

    Returns {results: [{goal, ok, answer_head, error}], duration_ms}.
    Anti-rekursi: dipanggil dari dalam sub-agen → tiap item gagal dengan
    pesan eksplisit (fail-closed), bukan error global.
    """
    if in_subagent():
        return {"results": [{"idx": i, "goal": str(g)[:120], "ok": False,
                             "answer_head": "",
                             "error": "anti-rekursi: sub-agen tidak boleh "
                                      "spawn sub-agen"}
                            for i, g in enumerate(goals or [])],
                "duration_ms": 0,
                # penanda level-atas agar pemanggil (worker) bisa
                # mempropagasikan alasan penolakan ke laporan induk
                "error": "anti-rekursi: sub-agen tidak boleh "
                         "spawn sub-agen"}
    if not isinstance(goals, list) or not goals:
        return {"error": "goals kosong"}
    goals = [str(g)[:500] for g in goals][:MAX_SUBAGENTS_PER_RUN]
    if not callable(runner):
        return {"error": "runner belum tersedia"}

    stamp = time.strftime("%H%M%S")
    out = []
    t0 = time.time()

    def _worker(idx_goal):
        """Jalankan runner DI THREAD PEKERJA dengan SOP + anti-rekursi.

        V38.1-fix: thread-local induk TIDAK mewarisi ke worker, jadi
        penanda dipasang di dalam worker itu sendiri.
        V38.2-SOP: runner menerima (sop_text, goal, ...) — SOP wajib; dan
        output worker diverifikasi kepatuhan SOP minimal."""
        i, g = idx_goal
        _tls.in_sub = True
        sop = build_sop(i + 1, g)
        try:
            r = runner(sop, g, f"sub_{stamp}_{i}",
                       SUB_MAX_ITERATIONS, SUB_WALL_SECONDS)
            r = r or {}
            answer = str(r.get("answer") or "")
            # Kepatuhan SOP minimal: harus ada penanda format laporan
            compliant = ("HASIL:" in answer and "STATUS:" in answer)
            return {"idx": i, "goal": g[:120],
                    "ok": r.get("ok", True) and bool(answer) and compliant,
                    "answer_head": answer[:300],
                    "sop_compliant": compliant,
                    "error": None if compliant else
                             "melanggar format pelaporan SOP"}
        except Exception as exc:
            return {"idx": i, "goal": g[:120], "ok": False,
                    "answer_head": "", "sop_compliant": False,
                    "error": str(exc)[:150]}
        finally:
            _tls.in_sub = False

    try:
        with ThreadPoolExecutor(max_workers=len(goals)) as pool:
            futs = [pool.submit(_worker, ig) for ig in enumerate(goals)]
            for fut in as_completed(futs):
                out.append(fut.result())
    finally:
        _tls.in_sub = False
    out.sort(key=lambda x: x["idx"])
    return {"results": out, "duration_ms": int((time.time() - t0) * 1000)}


SPAWN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "spawn_subagents",
        "description": (
            "Pecah tugas besar jadi 1-3 sub-tugas MANDIRI dan kerjakan "
            "paralel. Tiap sub-tugas harus spesifik & berdiri sendiri "
            "(sub-agen tidak melihat percakapan ini)."),
        "parameters": {"type": "object", "properties": {
            "goals": {"type": "array", "items": {"type": "string"},
                      "description": "1-3 sub-tugas spesifik"}}},
        "required": ["goals"],
    },
}
