# Changelog — Aeryn-Core

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
