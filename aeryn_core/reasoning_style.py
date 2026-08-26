"""V39.6 — Research-first reasoning + next-token prediction (keinginan Sen).

1. RESEARCH-FIRST: kalau goal butuh info yang tidak ada di memori/riwayat,
   Aeryn WAJIB riset dulu (web_search/web_read) SEBELUM menyusun jawaban.
   Bukan menebak dari pengetahuan umum lalu berharap benar.

2. NEXT-TOKEN PREDICTION: sebelum menjawab, Aeryn menulis "prediksi
   lanjutan" — apa yang paling mungkin user tanyakan/sbutuhkan SETELAH
   jawaban ini. Ditampilkan sebagai bagian kecil di akhir jawaban.

Keduanya diimplementasikan via system prompt injection (deterministik,
bukan doa) + detektor research-needed.
"""
import re

# Sinyal goal yang BUTUH riset web (info segar/faktual di luar kepala)
RESEARCH_SIGNALS = (
    "berapa", "kapan", "siapa", "dimana", "di mana", "harga", "cuaca",
    "terbaru", "terkini", "hari ini", "kemarin", "2025", "2026",
    "versi terakhir", "release", "rilis", "news", "berita",
    "apa itu", "jelaskan tentang", "bandingkan", "review",
    # V39.6c — tutorial/how-to juga butuh sumber (versi & command berubah)
    "cara install", "cara pakai", "how to", "tutorial", "setup ",
    "konfigurasi ", "migrasi ",
)

# Sinyal goal yang TIDAK perlu web (jawaban dari konteks/memori lokal)
LOCAL_SIGNALS = (
    "ingatkan", "pengingat", "namaku", "relasi kita", "kamu siapa",
    "hitung", "kalkulasi", "ingat ini", "catat:", "jam berapa",
    "statusmu", "kondisimu", "tools kamu",
)


def needs_research(goal: str, has_memory_context: bool = False) -> bool:
    """Deteksi apakah goal butuh riset web dulu."""
    g = str(goal or "").lower().strip()
    if not g:
        return False
    for s in LOCAL_SIGNALS:
        if g.startswith(s):
            return False
    if not any(s in g for s in RESEARCH_SIGNALS):
        return False
    # pertanyaan fakta + tidak ada konteks memori → riset
    return not has_memory_context


RESEARCH_FIRST_RULE = (
    "\n\n## PROTOKOL RESEARCH-FIRST (WAJIB)\n"
    "Kalau goal meminta FAKTA/informasi dan kamu TIDAK punya data cukup "
    "di memori/konteks:\n"
    "1. JANGAN langsung menjawab. JANGAN menebak.\n"
    "2. Lakukan RISET DULU: web_search (frasa kunci) → web_read "
    "(sumber terbaik).\n"
    "3. Setelah info CUKUP, baru susun ulang informasinya jadi jawaban "
    "yang rapi dan mudah disampaikan.\n"
    "4. Sebutkan sumbernya secara natural.\n"
    "Kalau setelah riset tetap tidak ketemu, bilang jujur apa yang belum "
    "ketemu — jangan mengarang."
)

NEXT_TOKEN_RULE = (
    "\n\n## NEXT-TOKEN PREDICTION (ciri khasmu)\n"
    "Di AKHIR jawaban (setelah inti), tambahkan prediksi singkat atas "
    "kelanjutan yang paling mungkin — apa yang kemungkinan besar akan "
    "user tanyakan/butuhkan selanjutnya, ATAU langkah logis berikutnya.\n"
    "Format: satu baris, diawali '➡️ ', maksimal 15 kata, bahasa kasual.\n"
    "Contoh: '➡️ Mau kubandingin sama alternatif lain, atau langsung "
    "praktek install?'"
)


def build_next_token_hint(answer_tail: str = "") -> str:
    """Fallback deterministik kalau model lupa menambahkan prediksi."""
    return ("➡️ Lanjutannya: tanyain detail yang kurang, atau minta aku "
            "praktekin langsung ya~")
