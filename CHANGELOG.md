# Changelog — Aeryn-Core

## V33-T (2026-08-25) — Web Reading & Hardening

- **Tool `web_read(url)`** via trafilatura: ekstraksi teks artikel bersih
  dari halaman web (judul/author ikut). Melengkapi web_search — loop riset
  lengkap: cari → baca → jawab. Tier safe, read-only, auto-promote.
- **json_repair di jalur tool-call**: argumen JSON rusak dari LLM tidak lagi
  menjatuhkan run — diperbaiki otomatis; kalau gagal total, model diminta
  kirim ulang dengan pesan jelas.
- Deps baru venv: trafilatura, json-repair (keduanya terverifikasi jalan
  di ARM64 proot).
- Verifikasi: 213 test green; live E2E "cari tahu apa itu react" →
  web_search + web_read → jawaban akurat dari sumber.

## V33-Fase2 (2026-08-25) — Observability & Self-Maintenance

- **`GET /metrics`** baru: uptime, statistik run (jumlah/error/timeout/wall
  time) ter-instrument di `_finish()`, plus status/success/fail per-tool.
- **`scripts/nightly_reflection.py`**: agregasi harian episode 24 jam —
  deterministik tanpa LLM (runs, success rate, top tools, error samples,
  pelajaran). Report JSON di `Personalisasi/nightly/YYYYMMDD.json`,
  ringkasan otomatis ke library Hermes via handoff.
- **Scheduler in-daemon**: thread daemon fire nightly tiap hari 03:00 WIB
  (20:05 UTC), fail-soft — refleksi gagal tidak mematikan daemon.

## V33 (2026-08-25) — Social Intelligence + Shared Brain

### Deteksi Sosial (F1)
- `_is_social_query()` ditulis ulang (daemon + social_generator): sinyal
  teknis positif (library/api/cara kerja/apa itu/ekstensi file) menang
  duluan; jalur sosial kini **wajib** sinyal relasional (greeting, pronoun,
  smalltalk). Rule "pendek dari 40 char = otomatis sosial" DIHAPUS — itu
  yang membuat pertanyaan knowledge pendek salah jalur.
- 14 negative-case test baru: "apa itu react?", "kamu pake library apa buat
  embedding?" → tool path, bukan social path.

### Sanitizer Context-Aware (F2)
- Prinsip baru via `_looks_machinelike()`: hanya output berbentuk mesin
  (code block, tool-call shape, key:value >=2, JSON literal null/true/false,
  prefix log `Error:`/`Warning:`) yang di-fallback.
- Kata umum (error/sistem/none) dalam kalimat natural TIDAK lagi membuang
  jawaban.

### Model Client (F3)
- Bug global-MODEL leak diperbaiki: client di-cache per-(provider,model)
  via `_CLIENTS` dict. Request default tidak lagi tertimpa request
  model-spesifik.

### Web Search
- Provider DuckDuckGo → **Bing scrape**: DDG diblok dari proot ini
  (SSL UNEXPECTED_EOF / ConnectionAborted). Redirect `bing.com/ck/a`
  param `u=a1<base64>` didekode jadi URL asli.

### Verifikasi
- Test suite 53 → **194 test**, semua hijau. Live smoke: social query
  deterministic 1-iterasi, knowledge query lewat web_search dengan hasil
  nyata (react.dev).

## V33-Hygiene (2026-08-25) — Struktur

- Import-graph audit AST dari semua entry point: 31 modul tak terjangkau.
- Klasifikasi aman: **26 modul zero-importer + zero-test diarsipkan**
  ke `_archive/v33-hygiene/` (git mv — restore mudah); **5 modul
  ber-test DIPARKIR** (dynamic_schema, memory_consolidation,
  memory_curator, multi_agent, verification_gate — fitur standby V30-V31).
- Regression pasca-arsip: 194/194 tetap hijau.

## V28 (2026-08-24) — Ketahanan Operasional

Naik versi setelah kemampuan (V27.4–27.7) dan ketahanan lengkap.

### Provider & Latensi
- **Groq = primary provider** (`openai/gpt-oss-20b` ~0.7s/call, fallback
  `qwen/qwen3.6-27b`) → OpenRouter :free → NVIDIA NIM. Run agentic normal
  turun dari ~2m35s ke **2–3.5s**.
- Fix Cloudflare Groq memblok User-Agent `Python-urllib` (error 1010/403) —
  custom UA header wajib.
- `gpt-oss`: `reasoning_effort=low` + JSON mode untuk planner (reasoning
  default "medium" menghabiskan token & membuat content kosong).
- 429 → rotasi kandidat **segera tanpa sleep** (sleep 8s + fallback NVIDIA
  = 25–35s per call).

### Streaming
- Loop agentic direfactor menjadi generator `_run_steps()`.
- Endpoint baru `POST /agent/run/stream` — SSE event `plan`/`tool`/`final`
  dipush real-time; `/agent/run` drain generator yang sama (backward-compat).

### Concurrency
- Lock per-session (`threading.Lock`) — dua run pada session yang sama
  diserialisasi, session berbeda tetap paralel. Race condition registry
  state hilang. Stress-test 6 paralel: max 89s → max ~12.6s.

### Test Suite
- `tests/test_core.py` — 13 test, mock ModelClient, zero network, 0.23s:
  episodic memory (4), reflection (2), emotion tone (2), planner heuristik
  (2), critic pass (3).

## V27 Internal (2026-08-24)

- **V27.1 Planner** heuristic-first untuk goal terstruktur (0 LLM),
  persist `plans/`, `GET /agent/plan/{sid}`.
- **V27.x Tool tiers**: terminal power tier sandboxed (whitelist read-only,
  tolak shell metachar, cwd lock); auto-promote native setelah parity.
- **V27.4 Memori Episodik**: jurnal append-only lintas-sesi
  (`Personalisasi/Database/episodes/`), recall keyword+recency,
  inject pengalaman relevan ke system prompt.
- **V27.5 Refleksi Pasca-Run**: analisis trace otomatis, digest di
  `GET /agent/reflections`, rekomendasi perbaikan mandiri.
- **V27.6 Critic Pass (div3)**: flag `?critic=true` — draft diverifikasi
  terhadap bukti tool sebelum final; revisi otomatis bila tidak cocok.
- **V27.7 Emosi→Nada**: tensor emosi session memengaruhi arahan gaya
  jawaban; kill-switch `AERYN_EMOTION_TONE=0`.

## V26 dan sebelumnya

Lihat riwayat sesi development.
