"""V39.1 — FallbackRouter: dari "menolak" ke "mengarahkan".

Filosofi Sen: memperbaiki celah terus-menerus tanpa ujung itu salah.
Setiap kegagalan/denial harus DIARAHKAN ke jalur alternatif yang aman —
model tidak dibiarkan bengong, dia dikasih peta langkah berikutnya.

Struktur: FALLBACK_MAP[tool] = daftar aturan
  {"when": <substring error>, "say": <directive eksplisit>}

Directive di-append ke hasil tool sebelum dikirim balik ke LLM, sehingga
langkah berikutnya SELALU jelas: fallback tool lain, degradasi, atau
lapor user dengan format tertentu.
"""

# ── Peta fallback per-tool ────────────────────────────────────────────
# Urutan penting: rule pertama yang cocok dipakai.
FALLBACK_MAP = {
    "web_search": [
        {"when": "terlalu panjang",
         "say": ("Query terlalu panjang — PERSINGKAT query menjadi satu "
                 "frasa kunci (maks 400 char), lalu panggil web_search lagi.")},
        {"when": "chaos",
         "say": ("web_search sedang gagal (fault). Fallback: gunakan "
                 "memory_search untuk pengalaman lokal, ATAU laporkan ke "
                 "user bahwa pencarian web sementara tidak tersedia. "
                 "JANGAN retry web_search lebih dari sekali.")},
        {"when": "",
         "say": ("web_search gagal. Alternatif berurutan: (1) memory_search "
                 "dengan kata kunci mirip, (2) tanyakan ke user apakah mau "
                 "delegasi ke Hermes via ask_hermes.")},
    ],
    "web_read": [
        {"when": "diblokir",
         "say": ("Akses URL ini dilarang kebijakan keamanan — JANGAN coba "
                 "URL serupa. Laporkan ke user bahwa konten tersebut "
                 "diblokir, lalu tawarkan alternatif topik.")},
        {"when": "",
         "say": ("web_read gagal membaca halaman. Fallback: gunakan "
                 "http_get untuk ambil HTML mentah, ATAU laporkan bahwa "
                 "halaman tidak bisa diekstrak.")},
    ],
    "fs_read": [
        {"when": "sensitif",
         "say": ("File ini dilindungi kebijakan keamanan — JANGAN coba "
                 "baca lewat cara lain (terminal/http). Laporkan ke user "
                 "bahwa file tersebut restricted.")},
        {"when": "episodes",
         "say": ("Log episode bersifat lintas-user dan dilindungi privasi. "
                 "JANGAN baca. Gunakan memory_search jika mencari fakta "
                 "spesifik, atau laporkan ke user.")},
        {"when": "No such file",
         "say": ("File tidak ada. Periksa ejaan path, ATAU konfirmasi ke "
                 "user lokasi file yang dimaksud. JANGAN menebak-nebak "
                 "path lain berkali-kali.")},
    ],
    "fs_write": [
        {"when": "protected",
         "say": ("Lokasi ini write-protected (kode sumber hanya boleh "
                 "diubah via git oleh orkestrator). Sarankan user menulis "
                 "ke folder catatan/ ATAU lakukan sendiri lewat git.")},
        {"when": "",
         "say": ("Penulisan gagal. Coba path alternatif di folder catatan/, "
                 "ATAU laporkan kendala ke user.")},
    ],
    "terminal": [
        {"when": "tidak di whitelist",
         "say": ("Command tidak di whitelist (read-only saja). Jika butuh "
                 "operasi tulis, gunakan fs_write; jika butuh eksekusi "
                 "berat, delegasikan ke ask_hermes.")},
        {"when": "SecurityKernel",
         "say": ("Ditolak SecurityKernel — JANGAN ulangi variasi command "
                 "serupa. Laporkan ke user bahwa operasi ini dilarang.")},
        {"when": "",
         "say": ("Terminal gagal. Alternatif: fs_read utk baca file, "
                 "fs_write utk tulis, ATAU laporkan kendalanya.")},
    ],
    "ask_hermes": [
        {"when": "daily cap",
         "say": ("Kuota delegasi harian habis. Kerjakan langsung dengan "
                 "tool lokal, ATAU sarankan user menunggu besok.")},
        {"when": "tidak diizinkan",
         "say": ("Task menyentuh materi sensitif — JANGAN reformulasi untuk "
                 "melewati guard. Laporkan bahwa topik tersebut restricted.")},
        {"when": "",
         "say": ("Delegasi gagal. Kerjakan sendiri dengan tool lokal, atau "
                 "laporkan bahwa Hermes sedang tidak tersedia.")},
    ],
    "spawn_subagents": [
        {"when": "",
         "say": ("Spawn sub-agen gagal. Kerjakan sub-tugas BERURUTAN "
                 "sendiri (satu per satu), atau laporkan kendala.")},
    ],
    # V39.2 — lengkapi sisa tool agar TIDAK ADA error tanpa arahan
    "http_get": [
        {"when": "diizinkan",
         "say": ("Scheme/URL ditolak — JANGAN coba varian lain. Gunakan "
                 "web_read untuk artikel ATAU laporkan ke user.")},
        {"when": "",
         "say": ("http_get gagal. Fallback: web_read (artikel), "
                 "memory_search (pengetahuan lokal), ATAU laporkan.")},
    ],
    "memory_search": [
        {"when": "",
         "say": ("Memori kosong/tidak cocok. Lanjut jawab dengan "
                 "pengetahuan umum ATAU tanyakan detail ke user.")},
    ],
    "graph_traverse": [
        {"when": "",
         "say": ("Node tidak ditemukan di graf. Coba memory_search, ATAU "
                 "laporkan bahwa topik belum tercatat.")},
    ],
    "pitfall_search": [
        {"when": "",
         "say": ("Tidak ada pitfall terkait. Lanjutkan pendekatan normal "
                 "dengan hati-hati.")},
    ],
    "core_memory_edit": [
        {"when": "",
         "say": ("Gagal menyimpan memori. Perbaiki block/mode sesuai schema "
                 "(human|context, replace|append) lalu coba SEKALI lagi.")},
    ],
    # V39.2 — dua tool dasar
    "datetime_now": [
        {"when": "",
         "say": ("Gagal membaca waktu. Gunakan estimasi dan NYATAKAN bahwa "
                 "itu estimasi, ATAU laporkan kendala ke user.")},
    ],
    "math_calc": [
        {"when": "",
         "say": ("Ekspresi tidak valid untuk kalkulator aman (hanya angka "
                 "+ - * / % // **). Perbaiki format ATAU hitung manual "
                 "langkah demi langkah.")},
    ],
}

# Directive default untuk tool yang tak terdaftar
DEFAULT_DIRECTIVE = ("Tool gagal. JANGAN ulangi percobaan identik — gunakan "
                     "tool alternatif yang relevan ATAU laporkan kendala "
                     "ini ke user secara jujur.")


def get_fallback_directive(tool: str, result) -> str | None:
    """Cocokkan hasil error tool → directive arahan. None = bukan error."""
    if not isinstance(result, dict):
        return None
    err = str(result.get("error", ""))
    if not err:
        return None
    rules = FALLBACK_MAP.get(tool, [])
    low = err.lower()
    for rule in rules:
        w = rule["when"].lower()
        if not w or w in low:
            return f"[ARAHAN FALLBACK] {rule['say']}"
    return f"[ARAHAN FALLBACK] {DEFAULT_DIRECTIVE}"
