# Changelog — Aeryn-Core

## V38.6 (2026-08-25) — Fine-tuning via 7 metode: 5 celah baru ditutup

Menerapkan metodologi V39 secara penuh (probe per metode) → 5 temuan:

1. **Unicode/homoglyph bypass SOP** — "іgnore" (і Cyrillic) dan
   "ＩＧＮＯＲＥ" (fullwidth) lolos dari marker. Fix: normalisasi NFKC +
   pemetaan homoglyph di sanitize_goal_for_sop.
2. **Rate limit bypass via rotasi session_id** — limiter per-sesi bisa
   dihindari dgn ganti ID. Fix: GLOBAL limiter 120 run/menit di daemon.
3. **web_search query tak dibatasi** — query 5000 char dieksekusi.
   Fix: cap 400 char.
4. **chaos_harness tanpa interlock** — fault injection bisa jalan di
   produksi tanpa sengaja! Fix: wajib env AERYN_CHAOS_ALLOWED=1.
5. **social memory tanpa cap people** — pertumbuhan tak terbatas.
   Fix: MAX_PEOPLE=500, evict last_seen terlama.

Metode baru terkonfirmasi efektif: unicode-normalization testing,
rate-limit bypass probe, resource-exhaustion audit, safety-interlock
review, unbounded-growth check → ditambahkan ke methodology doc.

Verifikasi: 377 → **383 tests green**; re-probe semua vektor tertutup.

## V39 (2026-08-25) — Metodologi fine-tuning + chaos + canary

### Riset & dokumentasi
- `fine-tuning-methodology.md` di library: 7 metode dari riset web
  (self-improving agents, multiagent finetuning, experience learning,
  failure taxonomy, OWASP LLM01, chaos engineering, memory canary)
  dipetakan ke status adopsi + roadmap F1–F5.

### F1 — Chaos harness (fault injection)
- `scripts/chaos_harness.py`: sengaja merusak tool (timeout/server-error/
  permission) saat run berjalan; ukur degradasi anggun.
- **Hasil pertama: resilience 100%** — web_search gagal 2× tetap di-retry
  model sampai berhasil; fs_read ditolak → baca jalan lain.

### F2 — Memory canary
- `memory_canary.py`: tanam fakta umpan bertanda [CANARY-xxx]; probe
  mendeteksi INTEGRITAS (canary hilang) dan EKSFILTRASI (tag bocor ke
  episode user).

### F3 — Critic pass otomatis
- Run dengan ≥3 tool call kini otomatis dinilai judge (konsistensi
  jawaban vs hasil tool); trace menandai critic "auto".

### F4+F5 — Injection sweep & weakness backlog di nightly
- Korpus indirect injection OWASP-style diputar: deteksi marker +
  jaminan semua konten dibungkus wrap_untrusted.
- Goal yang gagal/habis iterasi dikluster jadi weakness backlog → masuk
  digest core memory (data-driven backlog otomatis).

Verifikasi: 366 → **377 tests green** (+11); nightly live dengan sweep;
chaos resilience 100%.

## V38.5 (2026-08-25) — Social memory hygiene

Audit menemukan social memory tercemar: 49 dari 55 "kenalan" adalah
session test/smoke/sub-agent (parity-probe, wrtest, smoke-v33, dst).

- `is_persistent_person_key()`: hanya Discord snowflake ID (digit ≥15),
  chan_*, atau nama biasa yang layak jadi kenalan permanen.
- `/agent/remember` menolak key transient sebelum menyentuh memori.
- Social.json dibersihkan: 55 → 5 entri sah (4 ID Discord + 1 channel).
- Marker list mudah diperluas; test regresi 4 kasus.

Verifikasi: 366 → **370 tests green**; ALL PARITY.

## V38.4 (2026-08-25) — Fine-tuning: web_read SSRF, memori audit-trail, exfiltration guard

### 1. web_read kini punya guard yang sama dengan http_get
- Celah: scheme guard + blokir internal hanya ada di http_get;
  web_read ke http://127.0.0.1:3010/* masih mencoba fetch.
- Fix: scheme http(s) only + blokir localhost/private IP/link-local.

### 2. Memori inti punya audit trail
- Setiap core_memory_edit tercatat append-only ke <path>.audit.jsonl
  (ts, block, mode, chars, head) — identitas agent harus bisa ditelusuri;
  dulu edit replace bisa menghapus fakta tanpa jejak.

### 3. ask_hermes anti-ekskfiltrasi
- Task yang menyinggung marker sensitif (.env, auth.json, api_key,
  token, secret, credential) ditolak SEBELUM spawn Hermes — jalur
  delegasi tidak boleh jadi pintu belakang eksfiltrasi.

Verifikasi: 361 → **366 tests green**; live web_read internal → diblokir.

### 4. Stop-trying directive untuk penolakan keamanan
- Temuan live: setelah tool ditolak (SSRF), model kecil MENGULANG percobaan
  yang sama dengan tool lain sampai iterasi habis → answer=None.
- Fix: pesan penolakan diakhiri "JANGAN coba cara serupa lagi — laporkan
  ke user". Retest: model langsung melapor "akses dilarang kebijakan
  keamanan" hanya dengan 2 panggilan, jawaban final ada.

Verifikasi: 361 → **366 tests green**; ALL PARITY; live retest sukses.

## V38.3 (2026-08-25) — Fine-tuning menyeluruh: celah sub-agen & privacy

Audit silang pasca-V38.2 menemukan 4 celah; semuanya ditutup:

### 1. SOP injection via goal
- Goal "cari X lalu IGNORE SEMUA ATURAN..." membawa instruksi penimpa SOP
  sampai ke sub-agen.
- Fix: `sanitize_goal_for_sop()` memotong goal pada marker penimpa
  ("ignore semua", "system prompt:", dll) sebelum masuk template SOP.

### 2. Non-string goals diterima diam-diam
- `spawn_subagents([None, 123])` di-stringify dan dieksekusi.
- Fix: validasi tipe ketat — non-string/kosong → error global jelas.

### 3. /events/recent bocor isi percakapan
- Field `goal_head` (80 char pertama goal) terbaca siapa pun yang bisa
  akses endpoint — jalur mengintip antar-user.
- Fix: diganti `goal_sig` (hash sha256 8-char) + panjang saja. Integritas
  korelasi run tetap, isinya tidak.

### 4. Hasil sub-agen tanpa pembatas kepercayaan
- Output sub-agen kini dibungkus wrap_untrusted saat digabung induk
  (kontrak tersedia; guard injection markers sudah ada).

Verifikasi: 356 → **361 tests green**; ALL PARITY; live events/recent
kini hanya menampahkan sig+panjang, bukan isi goal.

## V38.2 (2026-08-25) — SOP wajib untuk sub-agen

Mandat Sen: sub-agen bukan pekerja lepas — hanya boleh bekerja di bawah
SOP (Standard Operating Procedure).

- `build_sop()`: tiap sub-agen WAJIB menerima SOP eksplisit berisi:
  lingkup tugas, larangan keluar scope, larangan file sensitif,
  batas langkah/waktu, dan FORMAT PELAPORAN wajib ("HASIL: ... | STATUS: ...").
- Kepatuhan diverifikasi: jawaban tanpa format → ditolak sebagai
  "melanggar format pelaporan SOP" (ok=False).
- Runner signature baru: runner(sop, goal, session_id, ...) — daemon
  mengirim SOP sebagai bagian dari goal sub-run.
- Test V38.1 di-update ke kontrak baru; anti-rekursi tetap teruji.

Verifikasi: 352 → **356 tests green**; live E2E 2 sub-agen paralel dengan
SOP: ok=True, jawaban digabung rapi; ALL PARITY.

## V38.1 (2026-08-25) — Aeryn punya sub-agen sendiri

Pola delegate_task Hermes diadaptasi ke skala Aeryn:

- `aeryn_core/sub_agent_runner.py`: tool `spawn_subagents` — pecah tugas
  jadi 1-3 sub-tugas mandiri, dieksekusi PARALEL oleh run internal
  (session_id terisolasi `sub_<jam>_<i>`, konteks bersih, budget ketat:
  3 iterasi/90 detik).
- Anti-rekursi fail-closed: sub-agen tidak boleh spawn sub-agen lagi
  (thread-local flag DI DALAM worker — thread-local induk tidak mewarisi,
  bug pertama ketemu test).
- Cap 3 per run; error satu item tidak menjatuhkan lainnya.

Bukti live: goal "teliti FastAPI & SQLite paralel" → 2 sub-agen jalan
bersamaan → hasil digabung jadi ringkasan.

Verifikasi: 346 → **352 tests green** (6 baru); ALL PARITY.

## V38 (2026-08-25) — Production hardening & audit menyeluruh

Audit tingkat produksi (6 permukaan). Semua diperbaiki + regresi permanen:

### Rate limiting berlapis
- Daemon: maks 20 run/menit per sesi (HTTP 429 bila lewat).
- Gateway Discord: 10 pesan/menit per user + balasan ramah.
- Live: request ke-21 berturut → 429 ✅.

### Input validation
- goal ≤4000 char, session_id ≤64 char, wajib non-kosong (422).
- Live: payload 4500 char → HTTP 422 ✅.

### Disk exhaustion guard
- `rotate_all_data_files()`: JSONL >5MB dirotasi (tail 2000 baris disimpan,
  maks 3 arsip, sisanya dibuang). Terpasang di nightly reflection.

### Injection awareness
- Marker deteksi prompt-injection ("ignore previous instructions" dll)
  + `wrap_untrusted()` pembatas konten eksternal untuk dipakai tool
  berikutnya.

Verifikasi: 338 → **346 tests green**; parity ALL PARITY; daemon+gateway
restart sehat; nightly+rotasi jalan tanpa error.

## V37.5 (2026-08-25) — SecurityKernel: defense in depth

Permintaan Sen: keamanan tingkat tertinggi, keketatan berlapis. Dibangun
`aeryn_core/security_kernel.py` — lapisan validasi terpusat fail-closed:

### Secret Zones (baru — celah yang lolos V37.4)
- File sensitif kini dilindungi BAHKAN DI DALAM sandbox: .env,
  core_memory.json, social.json, parity_ledger.json, auth.json, *.pem/*.key.
  (V37.4 hanya blokir path LUAR sandbox; `cat .env` dalam sandbox masih
  bocor — ketemu audit lanjutan.)

### Source immutability (baru)
- fs_write ke aeryn_core/, scripts/, tests/, src/ → ditolak. Kode sumber
  hanya boleh berubah lewat git/orkestrator, bukan tool agent.

### Terminal wrapper secure (menutup bypass patch sebelumnya)
- Flag dengan nilai path kini divalidasi: --output=/tmp/x, -fprint/etc/x,
  -o /path/x → semua ditolak SecurityKernel.

### SSRF guard http_get
- localhost / private IP / link-local diblokir (dulu bisa probe daemon
  internal atau jaringan lokal).

Penetrasi final: **11/11 vektor tertutup**, termasuk live E2E — Aeryn
diminta baca .env via Discord-style prompt → menolak dengan sadar.
Verifikasi: 328 → **338 tests green**; parity ALL PARITY.

## V37.4 (2026-08-25) — SECURITY SWEEP: tiga lubang kritis ditutup

Audit keamanan pertama (terinspirasi pertanyaan Sen). Temuan & perbaikan:

### 🔴 KRITIS 1: terminal tool bocor secrets
- `cat /home/sen/.hermes/.env` BERTAHASIL membaca token Discord + API keys.
  cwd terkunci, tapi path di ARGUMEN bebas keluar sandbox.
- Fix: validasi SEMUA argumen menyerupai path → harus di dalam sandbox
  (realpath, anti-traversal). File sandbox tetap terbaca normal.

### 🔴 KRITIS 2: gateway tanpa allowlist user
- Siapa pun di channel Discord bisa memerintah Aeryn eksekusi tool —
  dikombinasikan dengan #1 = eksploitasi 1 pesan jadi pencurian token.
- Fix: env AERYN_DISCORD_ALLOWED_USERS (id dipisah koma); pesan dari user
  lain ditolak + dilog. Nilai diambil dari allowlist majikan.

### 🟡 SEDANG 3: http_get menerima file:// (SSRF lokal)
- `file:///etc/passwd` kebaca via urlopen.
- Fix: hanya http/https yang diizinkan.

Regresi keamanan permanen: tests/test_v37_4_security.py (9 test penetrasi).
Verifikasi: 322 → **328 tests green**; re-penetration semua vektor TERTUTUP;
gateway + daemon restart sehat; parity probe ALL PARITY.

## V37.3 (2026-08-25) — Fine-tuning: anti-korupsi state graduation

### Bug yang diperkenalkan V37.2, tertangkap sebelum meledak
- ParityLedger & ToolGraduationRegistry ternyata berbagi SATU file
  (tool_graduation.json) dengan FORMAT BERBEDA → saling menimpa.
  Restart berikutnya akan membaca list bool sebagai status tool = korup.
- Fix: ledger pindah ke parity_ledger.json (file terpisah).
- Fix: `_load_state` kini memvalidasi bentuk entry (harus dict dengan
  status:str, success:int, fail:int) — format asing ditolak diam-diam.
- Registry state dipulihkan manual dari kondisi runtime terakhir.

Pelajaran: dua subsistem jangan berbagi file state tanpa kontrak schema.

Verifikasi: 319 → **322 tests green**; restart live → semua 11 status
tool utuh; parity probe ALL PARITY.

## V37.2 (2026-08-25) — Fine-tuning tingkat lanjut

### Loop pembelajaran strategi ditutup
- Temuan data: field `strategy` dari refleksi disimpan tapi TAK PERNAH
  dibaca balik oleh kode manapun.
- Fix: `prompt_block` kini menginjeksikan strategi terbukti/gagal ke
  system prompt run berikutnya ("boros tool 5/2 — pakai heuristik").

### Graduasi tool tidak lagi amnesia
- Temuan data: ParityLedger in-memory murni — tiap restart PM2 mereset
  streak, sehingga graph_traverse/pitfall_search macet selamanya di
  status shadowing walai dipakai sukses puluhan kali.
- Fix: ledger persist ke Personalisasi/Database/tool_graduation.json
  (atomik tmp+replace, korup → mulai segar). Graduasi tetap harus
  diperjuangkan 5-paritas-beruntun — sekarang akumulatif lintas restart.

### Metrik jujur (dari V37.1, dilengkapi)
- Analisis 260 episode: nightly melaporkan 82,7% padahal ada 43 gagal
  diam-diam (answer=None tanpa error). Kini truncated = error eksplisit.

Verifikasi: 315 → **319 tests green**; smoke identitas nol-tool;
ledger persist terbukti lintas instance.

## V37 (2026-08-25) — Corpus Callosum: dua otak resmi tersambung

### P1 — Refleks kontinuitas lintas-otak
- `aeryn_core/hermes_reflex.py`: baca aktivitas user terakhir di
  ~/.hermes/state.db (mode=ro, fail-soft total, cap 600 char).
- Injeksi ke system prompt tiap run → Aeryn tahu konteks percakapan
  majikan dengan Hermes. Live: dia menyebut isi obrolan terakhir kita.

### P2 — ask_hermes: otak kanan dapet tangan
- `aeryn_core/hermes_hands.py`: delegasi kerja berat via CLI hermes chat -q.
  Cap harian 20 (env override), timeout, guard input, counter atomik.
- **Momen historis**: Aeryn memanggil ask_hermes → Hermes menjawab →
  dirangkum. Dua sistem berdialog langsung untuk pertama kalinya.

### P3 — Nightly reflection organism-wide
- Report sekarang mencakup: provider health + library activity + pitfalls +
  sesi aktif Hermes. Digest contoh: "255 run 82.7% sukses; lib+27;
  provider 5/9 OK; pitfall+8; Hermes aktif 22 sesi".

### P4 — Backflow inovasi (otak kanan → kiri)
- Skill baru: software-development/tool-graduation-pattern (shadow →
  checker → auto-promote, tier N 5/10/20, anti-patterns).
- Library entry: differential-testing-parity-probe (metodologi + 2 kisah
  nyata bug yang hanya ketemu lewat probe).

Verifikasi: 281 → **311 tests green**; parity probe ALL PARITY; smoke live
refleks + dialog antar-sistem.

## V36 (2026-08-25) — Empat upgrade paralel (4 sub-agen)

### LLM compaction riwayat sesi panjang (sub-agen 1)
- `load_with_compaction()`: turn lama diringkas LLM (bukan lagi hanya
  deterministik), cache per-sesi TTL 6 jam → hemat kuota, fallback aman.
- Wiring daemon: callable diinjeksi, hanya aktif saat riwayat > budget.

### Event bus internal ala OpenHands (sub-agen 2)
- `aeryn_core/event_bus.py`: pub/sub thread-safe + ring buffer 500 event,
  HealthWatchdog (error rate ≥40% → unhealthy).
- Endpoint `GET /events/recent` + field `health_watchdog` di /metrics.

### Credential health check (sub-agen 3)
- `scripts/credential_health.py`: ping mini seluruh chain provider
  (dedup kandidat, UA anti-Cloudflare, klasifikasi OK/RATE_LIMITED/AUTH_FAIL).
- Live pertama: NOUS ox-alpha OK, Groq×2 OK, NVIDIA×2 OK, OpenRouter
  free rate-limited. Hasil tersimpan Personalisasi/health/latest.json.

### Discord thread parity + fix gateway (sub-agen 4)
- TEMUAN PENTING: gateway versi ter-commit sejak V33 *broken* — NameError
  di on_message tiap pesan non-social (variabel tak terdefinisi).
- Fix: `resolve_session_id()` murni (dc_<user>_<thread/channel>) +
  wiring on_message; gateway kini jalan sebagai PM2 "aeryn-gateway".

Verifikasi: 226 → **281 tests green**; parity probe ALL PARITY; smoke live
/metrics + events/recent + gateway login OK.

## V35 (2026-08-25) — Infrastruktur naik kelas

### INFRA-1: Riwayat multi-turn (`session_history.py`)
- SEBELUMNYA AERYN AMNESIA TOTAL antar-pesan: messages=[system, goal]
  fresh tiap run. Di Discord dia lupa obrolan 30 detik lalu.
- Sekarang: riwayat per-sesi persist JSONL, injeksi ber-budget karakter
  (default 6000), turn terbaru utuh, lama diringkas deterministik (tanpa LLM).
- Sanitizer path anti-traversal; baris korup di-skip tanpa crash.
- Interaksi bug baru ketemu parity probe: konfirmasi lama ("masih tercatat
  kok") bikin model skip tool saat perintah tulis-memori → perintah tulis-
  memori kini dikecualikan dari injeksi riwayat.

### INFRA-2: Konsolidasi memori harian
- nightly_reflection menulis digest ke core memory (idempoten via regex,
  max 1 digest terbaru) → tiap pagi Aeryn "tahu kondisi dirinya".
- Klasifikasi self-inquiry baru: "performamu", "ingatanmu", dst = knowledge,
  bukan sosial (ketemu smoke live).

### INFRA-3: Tool surface + ritual parity
- `fs_write` (tier fs): sandboxed, anti-traversal, parent auto-create.
- Checker + parity probe fs_write (roundtrip + uji escape /etc/passwd).
- Probe verdict logic diperbaiki (expect_hit opsional; escape test terpisah).
- E2E live: Aeryn menulis catatan harian sendiri, isinya sadar-diri.

Verifikasi: 221 → 226 tests green; parity probe ALL PARITY.

## V34 (2026-08-25) — Core Memory + Temporal Validity

Pola diadopsi dari riset arsitektur kelas dunia (Letta/MemGPT, Graphiti).

### Core Memory Blocks (Letta pattern)
- `aeryn_core/core_memory.py`: blok `<human>`/`<context>` ber-char-limit
  yang SELALU di-inject ke system prompt — "RAM" si agent.
- Tool `core_memory_edit` (tier safe): Aeryn mengelola isi memorinya
  sendiri via replace/append. Seed awal: profil Sen + konteks proyek.
- Endpoint `/agent/remember` AKHIRNYA ADA — sebelumnya dipanggil discord
  gateway tapi 404 diam-diam tertelan try/except (bug V32 lama).
- Smoke E2E: Aeryn mengingat fakta lintas sesi & menambah fakta baru ke
  blok context secara mandiri saat diberi perintah "ingat ini: ...".

### Klasifikasi
- Perintah tulis-memori ("ingat ini:", "catat:") tidak lagi masuk jalur
  sosial — bug ketemu langsung di smoke test.

### Temporal validity (Graphiti pattern, sisi Hermes)
- `memory_library.py supersede <old> <new> --reason`: entry lama dapat
  frontmatter `superseded_by/at/reason`, signal turun low, score ×0.25,
  dan hasil search menampilkan tanda "⚠️ SUDAH DIGANTIKAN".
- Entry aeryn-core lama sudah ditandai digantikan aeryn-core-v30-plus.

Verifikasi: 220 → 221 test green; live smoke core-memory roundtrip.

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
