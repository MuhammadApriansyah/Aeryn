# Changelog

All notable changes to Aeryn will be documented in this file.

---

## [65.0] — 2026-09-25

### ⚡ FASE 1 — Interface: non-blocking input + interrupt + multi-line

Berdasarkan riset agent UX (16 sumber, docs/research/): kloning Hermes TUI
behavior — rasa pakai agent modern.

**F1-1 — Queue non-blocking**: ketik saat agent jalan → antre → terkirim
OTOMATIS setelah turn (chat di background thread, prompt tetap aktif).
Dogfood PTY: submit saat jalan + antre + kirim otomatis + balasan ✓

**F1-2 — Ctrl+C interrupt mid-turn**: turn dihentikan ("⏹ dihentikan —
kerja sejauh ini tersimpan"), TUI tetap hidup; Ctrl+C 2x di prompt kosong =
keluar (ala Hermes). Key binding eager + SIGINT ignore.
Dogfood PTY: interrupt ✓ TUI hidup ✓

**F1-3 — Multi-line input**: backslash+Enter / Ctrl+J = newline,
Enter = submit (multiline ala Hermes docs).
Dogfood PTY: balasan dua baris utuh ✓

**Fix besar saat dogfood**: poll loop lama re-send request tiap 0.5s →
100+ request duplikat → 429 rate limit. Diganti sub-thread request (SEKALI
kirim, interrupt = cek flag, bukan re-send) — 429 hilang ✓

pytest: 620 passed

---

## [64.2] — 2026-09-25

### 💛 10 item bug/optimasi/pengembangan — full-autonomous + dogfood tiap item

Semua temuan dari laporan penggunaan potensi maksimal → dikerjakan berurutan
dengan dogfood (uji sebagai user nyata) per item:

**BUG (stabilisasi)**:
- **B1 — Fact store wiring**: fakta pribadi dari chat ("catet ya: motorku
  honda beat") → `personal_fact` di trust layer + embedding index →
  tersimpan PERMANEN. Dogfood: sesi baru → Aeryn ingat lintas sesi ✓
- **B2 — Reminder dedup**: dedup by resolved-time + substring — "besok
  jam 8 backup" = 1 reminder (dulu 3 bell). Multi-hari tetap 3. Bonus bug
  tersembunyi: 'besok 7' (tanpa kata jam) tidak terdeteksi → fixed.
  Dogfood: chat → 1 fakta scheduled ✓
- **B3 — Ledger description**: "beli kopi hitam 15k" → "kopi hitam"
  (bukan "transaksi" generik) + suffix rb + cat_map makanan.
  Dogfood: 3 kasus betul (minuman/makan/transportasi) ✓
- **B4 — Banner stats**: baca dari /skills + /agent-card + openapi
  (dulu /health field salah → 0). Label jujur: "Endpoints".
  Dogfood: "Endpoints: 654 Skills: 23 Niat: 0" ✓
- **B5 — Openapi bersih**: extended_router prefix /v1/dead → /v1/x
  (endpoint tetap jalan, 54 paths). Dogfood: dead=0, /v1/x jalan ✓

**OPTIMASI**:
- **O1 — Model routing per-kecepatan**: light/heavy heuristic + 404-model
  retry (anti fallback salah sasaran). Dogfood: ringan 2.5s / berat 5.6s ✓
  (catatan: 5x speedup butuh key non-thinking — hanya gemini-3.5 valid)
- **O2 — Context trimming agresif**: history -16 pesan + system cap 6000
  char. Dogfood 8-turn: 2.0s→1.5s growth -22% (dulu 8s→91s = +1037%) ✓

**PENGEMBANGAN**:
- **D1 — Proactive briefing 07:00**: deliver_briefing wired ke daily tick —
  jadwal+goal+catatan → Discord DM + notification otomatis.
  Dogfood: log "briefing pagi: sent=['discord:3f074f21', ...]" ✓
- **D2 — /voice**: mic HP → termux-speech-to-text → chat.
  Dogfood: "🎙 mendengar..." → error rapih saat tanpa suara; STT rc=0 ✓
  (izin RECORD_AUDIO di-allow)
- **D3 — Skill crystallization otomatis**: consolidate_experience wired ke
  daily tick — pattern 3x+ → skill baru harian.
  Dogfood: log "skill crystallized: ['auto_search_web_9654']" ✓

pytest: 620 passed

---

## [64.0] — 2026-09-25

### ⚙️ SERVICE TUNGGAL — Konsolidasi 5 service runsv → 1 service ^[[38;2;255;248;220m❯ ^[[0m






 
 ❯ chat · / command · Tab menu · ↑ history · /help semua                       
                                                                                
                           
[1m[38;2;205;127;50m╔══════════════════════════════════════════════════════════════════════════════╗[0m
[1m[38;2;205;127;50m║[0m [38;2;255;215;0m          Aeryn v63.1 (2026.9.24) - Self-Hosted Personal AI System          [0m [1m[38;2;205;127;50m║[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⣀⣀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  [38;2;255;248;220mTools: 0  Skills: 0  Niat: 0[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⢀⣠⣴⣾⣿⣿⣇⠸⣿⣿⠇⣸⣿⣿⣷⣦⣄⡀⠀⠀⠀⠀⠀⠀[0m  [38;2;184;134;11m/help untuk commands · /matter <teks> untuk niat[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⢀⣠⣴⣶⠿⠋⣩⡿⣿⡿⠻⣿⡇⢠⡄⢸⣿⠟⢿⣿⢿⣍⠙⠿⣶⣦⣄⡀⠀[0m  [38;2;255;191;0m127.0.0.1:3010[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠉⠉⠁⠶⠟⠋⠀⠉⠀⢀⣈⣁⡈⢁⣈⣁⡀⠀⠉⠀⠙⠻⠶⠈⠉⠉⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⡿⠛⢁⡈⠛⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⣦⣤⣈⠁⢠⣴⣿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣴⠦⠈⠙⠿⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣤⡈⠁⢤⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m╚══════════════════════════════════════════════════════════════════════════════╝[0m
  [2mSelamat datang di Aeryn! Ketik pesan atau /help untuk commands.[0m
  [2mcontoh: "ingetin besok jam 8 backup" · /status · /matter belajar rust · /help[0m
  [38;2;143;188;143m● api[0m │ [38;2;192;192;192m⏱ 0m00s[0m │ [38;2;138;122;74m⚙ scheduler[0m

^[[38;2;255;248;220m❯ ^[[0m

  [2msampai jumpa~[0m

Permintaan user: service runsv Aeryn terlalu banyak — disatukan.

**Sebelum**: 5 service runit (aeryn-api, aeryn-worker, aeryn-gateway,
aeryn-watchdog, aeryn-native-scheduler) = 5 runsv + 5 tee + 5 python
≈ 92MB / 19 proses.

**Sesudah**: 1 service ^[[38;2;255;248;220m❯ ^[[0m






 
 ❯ chat · / command · Tab menu · ↑ history · /help semua                       
                                                                                
                           
[1m[38;2;205;127;50m╔══════════════════════════════════════════════════════════════════════════════╗[0m
[1m[38;2;205;127;50m║[0m [38;2;255;215;0m          Aeryn v63.1 (2026.9.24) - Self-Hosted Personal AI System          [0m [1m[38;2;205;127;50m║[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⣀⣀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  [38;2;255;248;220mTools: 0  Skills: 0  Niat: 0[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⢀⣠⣴⣾⣿⣿⣇⠸⣿⣿⠇⣸⣿⣿⣷⣦⣄⡀⠀⠀⠀⠀⠀⠀[0m  [38;2;184;134;11m/help untuk commands · /matter <teks> untuk niat[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⢀⣠⣴⣶⠿⠋⣩⡿⣿⡿⠻⣿⡇⢠⡄⢸⣿⠟⢿⣿⢿⣍⠙⠿⣶⣦⣄⡀⠀[0m  [38;2;255;191;0m127.0.0.1:3010[0m
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠉⠉⠁⠶⠟⠋⠀⠉⠀⢀⣈⣁⡈⢁⣈⣁⡀⠀⠉⠀⠙⠻⠶⠈⠉⠉⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⡿⠛⢁⡈⠛⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⣦⣤⣈⠁⢠⣴⣿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣦⡉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣴⠦⠈⠙⠿⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣤⡈⠁⢤⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m║[0m [38;2;255;248;220m⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[0m  
[1m[38;2;205;127;50m╚══════════════════════════════════════════════════════════════════════════════╝[0m
  [2mSelamat datang di Aeryn! Ketik pesan atau /help untuk commands.[0m
  [2mcontoh: "ingetin besok jam 8 backup" · /status · /matter belajar rust · /help[0m
  [38;2;143;188;143m● api[0m │ [38;2;192;192;192m⏱ 0m00s[0m │ [38;2;138;122;74m⚙ scheduler[0m

^[[38;2;255;248;220m❯ ^[[0m

  [2msampai jumpa~[0m = 1 runsv + 1 supervisor + 5 anak yang
dikelola supervisor. Infra dasar (postgres, redis, sshd, ssh-agent, dbus)
tetap terpisah.

- **** — supervisor:
  start semua komponen → monitor → anak mati → restart backoff naik
  (2/5/10/20/30s, reset setelah stabil 60s)
- **Single-flight restart** (v64.1 fix): anti thread-pileup yang membuat
  spawn anak duplikat tiap poll cycle — ditemukan saat dogfood (restart #194)
- **State file** : pid/alive/restarts
  per komponen, dibaca monitoring eksternal
- **Log per komponen tetap** ke file log lama (aeryn-api.log dst) —
  pattern log file per service dipertahankan (tanpa WhatsApp)
- **SIGTERM aman**: stop semua anak → tunggu → keluar (runit restart)

Bukti: 5 komponen alive (api/worker/gateway/scheduler/watchdog) ✓
chat nyata ✓ scheduler ticks ✓ restart-resilience (bunuh -9 → restart) ✓
pytest: 620 passed

---

## [63.1] — 2026-09-25

### 💛 UX PASS — CLI/TUI ramah pengguna (dogfood PTY-driven)

Dogfood user: "bingung pake nya". 5 perbaikan UX ala Hermes:

- **Spinner "Aeryn berpikir..."** saat chat nunggu LLM (thread sederhana)
- **Typo tolerance**: "/stat" → "maksud kamu /status?" · "/costr" → /cost ·
  "/mater" → /matter (prefix + substring + edit-distance ≤1 + deletion)
- **Arg hint ramah**: command butuh argumen tanpa arg → tampil format +
  contoh langsung ("/matter belajar rust tiap malam")
- **/help quick-start**: "Cara pakai" 3 baris di atas daftar — pemula
  langsung paham (pesan biasa = chat, /command = slash)
- **TUI bottom toolbar** (prompt_toolkit, ala Hermes statusbar):
  "❯ chat · / command · Tab menu · ↑ history · /help semua" — selalu terlihat
- **Welcome + contoh pemakaian** di TUI & REPL sebelum prompt pertama

Bukti PTY: typo_suggest ✓ spinner ✓ welcome ✓ toolbar ✓ (render TTY)
pytest: 620 passed

---

## [63.0] — 2026-09-25

### 🖥️ CLI/TUI v63 — REWRITE penuh meniru Hermes (dogfood-driven)

Dogfood PTY menemukan: TUI lama input beku + tidak bisa dipakai interaktif,
command sedikit & tidak rapih. Rewrite total `console/aeryn_cli.py` (916 baris):

- **Visual ala Hermes** (skin default gold & kawaii):
  banner ╔═╗ gold + braille hippo art + summary (tools/skills/niat/api),
  prompt ❯ (#FFF8DC), input rule #CD7F32, response border ⚕ gold,
  status bar satu baris (api · durasi · scheduler) ala _build_status_bar_text
- **35 slash commands dalam 5 kategori** ala COMMANDS_BY_CATEGORY:
  Session (12) / Configuration (8) / Info (7) / Tools & Skills (6) / Exit (2)
  — /help kategorikal + filter query ala Hermes
- **TUI prompt_toolkit** (seperti Hermes): fixed input area + patch_stdout +
  InMemoryHistory (arrow-up) + slash completion menu (deskripsi tiap command)
  + status bar bawah tiap turn
- **Chat via /v1/chat** (agent loop penuh: trust + memory + tools) dengan
  fallback /chat; response border Hermes-style
- REPL fallback tanpa prompt_toolkit + subcommand CLI (help/chat/status/goals/matter)

### 🐛 Fix chat 503 (root cause via reasoning store)
- Gejala: /v1/chat 503 "Kuota/kredit habis" — misleading
- Bukti reasoning store: gemini 404 → openrouter 402 → deepseek 402
- Root cause: proses API lama (orphan) jalan dengan env/model stale —
  gemini-3.5-flash-lite valid di venv test via /chat/completions OpenAI-compat
- Fix: kill ALL orphan + sv restart bersih → chat normal
  ("Hadir, siap lanjut bos.")

### Uji (dogfood PTY — seperti user asli)
- TUI: banner + /scheduler + chat nyata + /cost + status bar — semua jalan
- REPL: /whoami /status /scheduler /cost /history /goals + chat — semua jalan
- pytest: 620 passed

---

## [62.26] — 2026-09-24

### 🎉 RM4-RM10 — Roadmap Capability Growth + CLI/TUI Upgrade (selaras Aeryn_Identity.md)

Ke-7 roadmap Aeryn_Identity.md §15 dikerjakan full-autonomous + E2E nyata
(zero test double). Semua selaras North Star: personal scope, self-hosted,
user-governed.

### RM4 — Scheduler daemon → Rust
- `AerynScheduler` (pyo3): cron tick + decay harian digabung satu thread native
- `native_scheduler_daemon.py` sebagai runit service TERPISAH (service ke-10)
  — in-process memblokir uvicorn (GIL contention dari callback PG sync)
- `/scheduler/health` baca dari state file (daemon terpisah)
- E2E: running:true, tick 60s, daily jalan, errors:[] + API normal

### RM5 — Embedding lokal Termux
- `local_embedder.py`: ORT InferenceSession (model.onnx 90MB
  all-MiniLM-L6-v2, CPU provider) + tokenizers Rust
- `embed()` ORT dulu → fallback proot aman
- E2E: cold 0,57s vs proot 82s = **145x lebih cepat**, warm 10ms

### RM6 — Tools sensor dunia
- `sensor_tools.py`: weather (open-meteo) + calendar_read (ZSET) + location
  (termux-api, butuh izin — error eksplisit)
- `/sensor/*` endpoints + internal_tools
- E2E: 33.8°C hujan lokal ringan + 5 upcoming

### RM7 — Long-horizon planning wired
- `long_horizon_runner.py`: goal besar → plan → decompose → execute bertahap
  + checkpoint (resume lintas sesi/hari)
- Fix bug lama: `get_task` query SELECT tanpa `FROM tasks` + subtask key
  mismatch + asyncio.run
- `/horizon/*` endpoints — E2E: 1/1 done + checkpoint after

### RM8 — Experience learning depth
- `experience_learning.py`: failure → pitfall + success pattern →
  crystallize otomatis (skill dari pengalaman)
- `/learning/*` endpoints + daemon daily consolidate
- E2E: pattern 3x → skill `auto_search_web`

### RM9 — Multimodal input
- `multimodal_tools.py`: voice STT (termux-api) + camera + vision (LM,
  error eksplisit HITL)
- `/multimodal/*` endpoints — E2E: error eksplisit tanpa mic/izin

### RM10 — Browser/computer interaction
- `browser_tools.py`: open (termux-open-url, HITL user-visible) + read
  (requests + robots.txt politeness) + computer_status
- `/browser/*` endpoints — E2E: example.com read + battery 70%

### CLI/TUI upgrade (comot pola Hermes, sesuaikan untuk Aeryn)
- CLI 11 → **17 commands**: + ledger, sensor, matter, briefing, horizon, cost
- TUI 3 → **7 panel**: + keuangan, cuaca, scheduler, cost
- TUI slash commands (Hermes-style): /chat /status /cost /ledger /sensor
  /briefing /horizon /matter /help
- Chat CLI/TUI → `/v1/chat` (agent loop penuh), fallback `/chat`

### Uji penuh (E2E menyeluruh)
- **16/16 grup endpoint OK** (health, scheduler, chat, ledger, briefing,
  sensor, learning, cost, A2A, horizon, matter, observability)
- pytest: **620 passed** (Termux aarch64)

---

## [62.1] — 2026-09-20

### 🎉 Fase AL + FW1-4 + IN1-3 — Self-Reporting AI OS (Termux native + AlmaLinux worker)

Aeryn kini **self-reporting**: tahu kondisi dirinya, melapor saat sakit, dan
punya ecosystem 17 skills. Semua fase dikerjakan full-autonomous.

#### Fase AL — AlmaLinux Rootfs (glibc-worker)
- **AL1**: AlmaLinux 10.2 (Lavender Lion) rootfs hidup via proot — Python 3.12.14 + dnf 4.20 OK, DNS bound
- **AL2**: Bukti konsep wheel manylinux aarch64 PREBUILT — pydantic-core 2.49.0 + numpy ter-install detik (bukan 20 menit CFS)
- **AL3**: Cross-use terbukti — import numpy/pydantic_core jalan di dalam AlmaLinux-worker
- Root cause terpecahkan: `LD_PRELOAD=` (matikan termux-exec bionic) + `-r` path absolut + SIGSYS/SIGSYS seccomp via proot translasi

#### Fase FW1 — Wire Internal Tools → Chat
- `aeryn_core/platform/internal_tools.py`: 5 tools nyata (memory_search, graph_traverse, graph_status, pitfall_search, battery)
- Ter-register di 2 registry: plugin_registry (chat router) + aeryn_core.tools (AgentLoop)
- Guardrail policies READ_ONLY untuk 5 tools (deny-by-default tetap untuk yang lain)
- **E2E terverifikasi**: "Cek baterai dan cari di memori tentang watchdog" → tool call + persona response hidup

#### Fase IN1 — Redis Job-Queue
- `aeryn_core/platform/redis_queue.py`: push/pop/length/stats via redis-py (tahan restart — job persist di redis)
- `aeryn_core/platform/queue_worker.py`: worker daemon (chat/shell handlers)
- Runit services: redis + aeryn-worker (auto-start via runsvdir)
- **E2E terverifikasi**: push job shell → worker execute → output tertulis

#### Fase IN2+IN3 — Watchdog Self-Reporting
- `aeryn_core/platform/watchdog.py`: monitor aeryn-api/postgres/redis tiap 60s
- Alert ke Sen via termux-notification (DOWN 2x beruntun → ALERT; recovered → ✅)
- IN3: kejadian dicatat ke bitemporal facts (PG) — riwayat jadi memori Aeryn
- **E2E terverifikasi**: tick api=True pg=True redis=True + NOTIFY=True + record_fact ke PG OK

#### Fase FW3 — MCP Server (Official SDK)
- `aeryn_core/mcp/local_server.py`: FastMCP streamable-http (JSON-RPC asli)
- 6 tools: battery, memory_search, graph_status, pitfall_search, redis_stats, api_health
- **E2E terverifikasi**: handshake + tools/list + tools/call redis_stats → real data

#### Fase FW4 — Ecosystem Seed (17 skills)
- `aeryn_core/skills/seed_fw_skills.py`: 8 skills FW-era (Redis Job Queue, Watchdog Monitoring, MCP Server, AlmaLinux Worker, Memory Graph Traverse, Pitfall Database, Self Modify, Termux Body)
- Total 17 skills aktif di crystallized_skills (9 core + 8 FW-era)

---

## [62.0] — 2026-09-03

### 🎉 Major — Agent Framework Complete (Fase 1-8)

Aeryn graduated from "agent core" to **production-grade agent framework**.
8 phases built from validated research (OpenTelemetry GenAI, AWS/Azure playbook,
arXiv agent evaluation/security papers).

#### Fase 1-4: Agent Core
- **Agent Loop**: LLM → Tool → Response cycle with session history
- **5 Core Tools**: bash, file_read, file_write, file_search, web_search
- **5 Cognitive Divisions** + keyword-based routing
- **Plugin System**: dynamic tool loading (calculator plugin example)
- **Memory**: recall, write, context window
