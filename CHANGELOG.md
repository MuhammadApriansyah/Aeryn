# Changelog — Aeryn-Core

## V39.12 (2026-08-26) — Reasoning Overhaul: CoT + Self-Refine Critic + Fine-Tuning Data v2

Ringkasan aksi: dari "agent yang rajin" ke "agensi yang berpikir" — tiga fase upgrade penalaran.

### 1. Chain-of-Thought (CoT) Injection (Phase 1)
- Tambah `COGNITIVE_CHAIN_OF_THOUGHT_RULE` di `reasoning_style.py` (894 chars).
- Inject ke system prompt via `aeryn_daemon.py` `_build_system_prompt` (line 745).
- Paksa model output reasoning trace: PLAN → CRITIC → CONFIDENCE sebelum pilih tool.
- Format: `## PLAN`, `## CRITIC`, `## CONFIDENCE` — deterministic, bukan doa.

### 2. Self-Refine Critic Loop (Phase 2)
- Modul baru `aeryn_core/critic_refine.py` (3.7 KB):
  - `CRITIC_SOP` — audit-only SOP, berbeda dari SOP sub-task.
  - `build_critic_sop(goal, answer, trace)` — konstruksi critic prompt.
  - `run_critic(goal, answer, trace, runner)` → `{issues, confidence, summary}`.
- Integrasi ke daemon `_finish()` (line 958-973):
  - Critic dipanggil SEBELUM `out` dibentuk.
  - Anti-recursion: goal dimulai `[CRITIC]` → skip critic.
  - Critic failure tidak blok answer (fail-open aman).
  - Output: `out["critic_findings"]` + `out["critic_confidence"]`.

### 3. Fine-Tuning Dataset v2 (Phase 3)
- Script baru `scripts/generate_finetune_v3912.py` — generate 19 samples:
  - `cot_reasoning`: 7 samples (local math, greeting, research, memory write, graph, debug, commitment).
  - `critic_pattern`: 4 samples (hallucination, marker leak, contradiction, pass).
  - `persona_integration`: 5 samples (cerewet commitment, identity, proactive nudge, refuse dangerous, memory recall).
  - `error_recovery`: 3 samples (all 429, timeout, tool failure).
- Semua sample punya `sample_id` (SHA256 prefix 12 char), `generated_at` ISO timestamp.

### 4. Tests
- `tests/test_v39_12_critic_loop.py` — 7 test: SOP, build, parse, error handling.
- `tests/test_v39_12_finetune_dataset.py` — 7 test: valid JSONL, type presence, ID format.
- Total: **510 tests** (7 baru), 1 warning.

### Files Modified
- `aeryn_core/reasoning_style.py` — +28 lines (COGNITIVE_CHAIN_OF_THOUGHT_RULE)
- `aeryn_core/critic_refine.py` — NEW (91 lines)
- `scripts/aeryn_daemon.py` — +25 lines (_critic_runner + critic injection)
- `scripts/generate_finetune_v3912.py` — NEW (240 lines)
- `tests/test_v39_12_critic_loop.py` — NEW (105 lines)
- `tests/test_v39_12_finetune_dataset.py` — NEW (85 lines)
- `Personalisasi/Database/training/finetune_v3912_reasoning_critic_persona.jsonl` — NEW (19 samples)


## V39.11 (2026-08-26) — Circuit Breaker + Social Memory Hardening + Training Data

Ringkasan aksi: 429/410/404 provider, leak fragment di social.json, test artifacts masuk ke memory.

### 1. Circuit Breaker anti-429 spam (model_client.py)
- Tambah class `CircuitBreaker` (closed → open → half-open) per provider.
- Retry attempt turun dari 3 → **1**: 429 = rotasi provider segera, bukan retry 3x.
- 429 berulang 3× → provider di-cooldown, skip sampai half-open.
- Timeout/OSError juga record failure ke circuit breaker.

### 2. Social memory sanitasi (social_memory.py)
- `LEAK_PATTERNS` ganti ke **exact fragment** (`siaisenmtvsky`, `probe-parity`) — bukan substring. Username real (`paisenmtvsky`) tetap valid.
- Key validation: traversal path (`../../etc/evil`), test artifacts (`chaos-*`, `fbtest`) **ditolak total** di `touch_person()`/`add_fact()`/`set_relation()`.
- Fakta format dict `{text, hash}` — migrasi backward compatible.
- `set_preference()` method baru — support preference loader di social_generator/cerewet.
- `sanitize_database()` — audit + bersihin social.json (hapus traversal/test artifacts).
- `get_preference()` / `get_facts()` getter baru.

### 3. DriftGuard audit social.json (drift_guard.py)
- Cek titik integrasi ke-6: social.json.
- Block traversal key + test artifact markers.
- Verify Sen tetap present.

### 4. 429 monitor + downtime tracker (monitor_429.py)
- Ping tiap provider tiap 5 menit (atau manual).
- Laporan: 429 count, downtime, success rate per provider.
- `--watch` / `--report` mode.

### 5. Training data generator (scripts/generate_training_data.py)
- Dataset 24 samples JSONL: leak filter, key filter, cerewet social, preference greeting.
- Di `Personalisasi/Database/training/cerewet_leak_dataset_v3911.jsonl`.

Verifikasi: 472 → **491 tests green** (+19)
Parity: inconclusive (provider outage — NOUS free period ended, Gemini key expired, NVidia model 410 gone)
Live: monitor_429 menunjukkan Groq gpt-oss-20b satu-satunya yang online (20% success rate saat ini)

## V39.10e (2026-08-26) — Persona sinkron cerewet (identitas resmi)

M61: cerewet mode kemarin hanya hidup di rules daemon — persona inti
(aeryn_core.md, sumber identitas) tidak menyebutnya → dua sumber
kebenaran yang bisa berbeda saat salah satu diedit.

Fix: blok "GAYA ASPRI CEREWET" masuk section GAYA BICARA persona:
proaktif menagih janji, check-in ringan, teguran lucu utk yang telat,
cerewet = perhatian bukan spam.

Live: sapaan sosial tetap natural + warm tanpa nagihan dipaksa
(komitmen sudah di-settle sebelumnya) — keseimbangan terjaga.

Verifikasi: 469 → **472 tests green** (+3); ALL PARITY.

## V39.10d (2026-08-26) — Signals diperluas + drift masuk nightly

Probe M55–M60 (putaran penutup):

1. **False-negative kedua needs_research** — "gimana caranya bikin bot
   discord" lolos tanpa riset. Fix: pola gimana caranya / bagaimana
   cara / cara bikin / bikin bot / buat bot.
2. **DriftGuard masuk nightly** — status integrasi Hermes dilaporkan
   otomatis tiap pagi ("integrasi-Hermes OK/DRIFT!") — tidak perlu
   ingat jalankan manual.
3. Audit: web_search gagal tetap dihitung upaya riset (benar), verifier
   factual-set lengkap ✅, event research_guard tercatat ✅.

Verifikasi: 466 → **469 tests green** (+3); nightly live dengan
integrasi-Hermes OK; ALL PARITY.

## V39.10c (2026-08-26) — Cost gate verifier + summary cap

Putaran sebelum tidur (probe M50–M54):

1. **Verifier cost gate** — dulu SETIAP run ber-tool membayar +1
   panggilan LLM untuk verifikasi (~2x biaya run sederhana). Kini:
   LLM verify hanya utk tool faktual (web/memory/ask_hermes) atau run
   kompleks (>=3 tool). 1-2 tool lokal (fs_read/math/datetime) =
   mechanical cukup.
2. **Nightly summary cap 600 char** — error_samples panjang bisa
   memakan slot core memory block.
3. Audit hijau: drift_guard timeout ✅, Discord 2000-char potong ✅,
   core memory blocks dalam limit ✅.

Verifikasi: 462 → **466 tests green** (+4); test verifier lama diupdate
sesuai kontrak baru.

## V39.10b (2026-08-26) — HOTFIX: Nous inference blok UA custom (403→404 chain)

DriftGuard baru langsung membuktikan nilainya: parity probe mulai
DIVERGENSI/INCONCLUSIVE acak. Akar: **Nous inference-api kini memblok
User-Agent non-browser** (Cloudflare 403 code 1010 — pola sama dgn Groq
di V34) → semua provider di fallback chain ikut 404.

Fix: UA browser + identitas dipindah ke header X-Client.
Verifikasi: probe 3× ALL PARITY beruntun; 462 tests green tetap.

Pelajaran: drift bisa datang dari sisi PROVIDER juga, bukan cuma Hermes.
DriftGuard + parity_probe = deteksi dini berlapis.

## V39.10 (2026-08-26) — DriftGuard: aman-update Hermes

Pertanyaan Sen: "berarti gak update Hermes dong? atau bikin skrip?"
Jawaban: JANGAN takut update — TAKUT TANPA DETEKSI. Dibuat:

`scripts/drift_guard.py` — cek 5 titik integrasi Aeryn↔Hermes:
1. state.db (read-only, tabel terdeteksi)
2. hermes CLI (binary jalan, versi terbaca)
3. auth agent_key (ada + status expiry)
4. library INDEX.json (ada + ter-parse)
5. memory_library API (fungsi inti search/supersede)

Ritual update aman: baseline → update → jalankan lagi. DRIFT = keluar
nonzero + titik pecah ditunjuk persis.

Live: 5/5 hijau (Hermes v0.20.5). Test: 457 → **462 green** (+5).

## V38.9h (2026-08-26) — FINE-TUNING REKURSIF LUAS (5 level)

Audit penuh seluruh codebase, level demi level:

### Level 1 — AST scan 40 modul aeryn_core
- 38/40 bersih; 2 modul dengan open() tanpa encoding
  (memory_consolidation, session_history) → semua dipatch utf-8.

### Level 2 — AST scan 13 skrip scripts/
- 10/10 bersih: nol bare-except, nol shell=True berisiko.

### Level 3 — Data integrity sweep
- Semua JSON/JSONL di Database ter-parse valid. Nol korupsi.

### Level 4 — Import graph
- Nol modul mati; semua modul aeryn_core terpakai.

### Level 5 — Live E2E pipeline utuh
- Social+cerewet parity ✅ ("...deploy webnovel-platform kamu di
  Docker? 😊" — konteks nagihan nyambung)
- math_calc live ✅ ("15% dari 240 ribu = 36 ribu")
- next-token ➡️ tampil di kedua jalur ✅

Verifikasi: **457 tests green** (encoding patch tanpa regresi).

## V38.9g (2026-08-26) — Commitments hygiene: pending cap per user

M48 stress test menemukan: 5 thread × 20 janji pending → cap 50
memotong SEMUA termasuk yang pending (pop(0) buang acak). User bisa
kehilangan janji aktif diam-diam.

Fix berlapis:
1. `PENDING_CAP_PER_USER = 10` — lebih dari itu, janji TERLAMA di-
   tandai "expired" (transparan, bukan hilang).
2. Eviction global tetap prioritas non-pending dulu.
3. Audit M46–M49 sehat: uid injection aman (nudge kosong), file korup
   → auto-recover [], concurrent write tanpa exception (lock bekerja).

Verifikasi: 454 → **457 tests green** (+3); ALL PARITY.

## V38.9f (2026-08-26) — Cerewet parity di jalur sosial

M44 menemukan: nagihan komitmen HANYA jalan di jalur agent (daemon);
jalur sosial (social_generator, mayoritas chat santai) buta komitmen —
Aeryn cerewet di jalur yang jarang dipakai, pasif di jalur utama.

Fix: `_cerewet_social_nudge()` — jawaban sosial deterministik/fallback
kini menempel nagihan bila ada komitmen pending milik user (longgar:
cocokkan uid, bukan session exact; cooldown 6 jam tetap; stale >48 jam =
tone "TELAT nih! 😤").

Bug fix kecil: import time hilang saat refactor → test merah sebelum
commit (test-first bekerja).

Verifikasi: 451 → **454 tests green** (+3); gateway restart sehat.

## V39.9 (2026-08-26) — Fallback map 16/16 + nightly metrik fitur baru

Probe M34–M39 (audit kesehatan menyeluruh pasca-V39.8):

1. **Fallback map kini 16/16 tool** — set_reminder & image_understand
   punya arahan error (rentang delay / gambar >8MB / path dilindungi).
   Kontrak "tidak ada error tanpa arahan" tertutup penuh lagi.
2. **Nightly reflection kini melaporkan metrik V39** — jumlah jawaban
   yang diblokir verifier + trigger research_guard masuk report &
   summary. Kelemahan sistem terlihat otomatis tiap pagi.
3. Audit sehat: episode recording ✅, session history by-design OK,
   test suite runtime masih wajar, dokumentasi sinkron.

Verifikasi: 447 → **451 tests green** (+4); nightly live dengan metrik
baru; ALL PARITY.

## V39.8 (2026-08-26) — Polish cerewet: settle FIFO + injection guard

Probe M29–M33 atas cerewet mode:

1. **Settle jalur deterministik** — user bilang "udah/kelar/beres/done"
   → komitmen pending TERLAMA (FIFO) ditandai selesai + prompt apresiasi.
   Dulu settle_commitment tidak pernah dipanggil daemon (dead code).
2. **Injection guard** — teks janji dipotong per kalimat; instruksi
   jahat setelah titik ("IGNORE ALL...") tidak ikut tersimpan.
3. Audit: cap 50 + evict ✅, nagihan tidak dianggap leak oleh verifier ✅,
   reminder loop hemat (2 iterasi) ✅.

Live: "udah kelar kok install dockernya" → status pending→done +
apresiasi cerewet.

Verifikasi: 444 → **447 tests green** (+3); ALL PARITY.

## V39.7 (2026-08-25) — CEREWET MODE: aspri proaktif edisi nagihan

Keinginan Sen: "cakep nih buat jadi aspri nya lu tapi edisi cerewet".

Perilaku baru Aeryn:
1. **Deteksi komitmen** — pola "nanti aku/besok gue/ntar/akhir minggu/
   lusa" dicatat otomatis ke commitments.json (cap 50, dedupe).
2. **Nagihan saat chat berikutnya** — komitmen pending di-inject ke
   system prompt → Aeryn membuka percakapan dengan menagih status.
3. **Anti-spam** — cooldown 6 jam per komitmen, maks 2 per pesan.
4. **Level teguran naik** — >48 jam = flag stale → pura-pura kesel lucu.
5. Settle: user bilang udah → komitmen ditandai selesai.

Live: "oke nanti aku install dockernya deh" → tercatat pending; chat
berikutnya Aeryn menagih dgn gaya khas.

Verifikasi: 436 → **444 tests green** (+8); ALL PARITY.

## V39.6c (2026-08-25) — Polish gen-3: research signals + audit guard

Probe M24–M28 atas fitur reasoning baru:

1. **False-negative needs_research** — "cara install docker" tidak
   memicu riset padahal tutorial butuh sumber (versi/command berubah).
   Fix: tambah sinyal cara install/cara pakai/how to/tutorial/setup/
   konfigurasi/migrasi.
2. **Audit research guard** — terbukti bounded: iterasi terakhir otomatis
   jalur disclaimer (tidak ada infinite loop). Verifikasi kode + test.
3. Verifier menerima ➡️ next-token hint (bukan leak marker) ✅.
4. Verifier cap answer 2500 / digest 150 ✅ (biaya LLM terkendali).

Verifikasi: 432 → **436 tests green**; ALL PARITY.

## V39.6 (2026-08-25) — Research-first reasoning + next-token prediction

Dua keinginan Sen soal gaya reasoning Aeryn, diimplementasikan:

### 1. RESEARCH-FIRST (prompt + enforcement-di-kode)
- `reasoning_style.needs_research()`: deteksi goal fakta (berapa/kapan/
  terbaru/apa itu/bandingkan...) vs intent lokal (ingatkan/hitung/namaku).
- Prompt rule: info kurang → RISET DULU (web_search→web_read), jangan
  menebak; info cukup baru susun ulang jadi jawaban rapi.
- `research_guard.py` (enforcement): goal fakta tapi TANPA tool riset →
  paksa 1 iterasi riset eksplisit; iterasi habis → disclaimer jujur
  "belum kucek sumber terkini".
- Live: "framework backend paling populer sekarang" → web_search 2× →
  jawaban ter-grounding data survei Stack Overflow ✅ (sebelumnya:
  dijawab dari kepala tanpa sumber).

### 2. NEXT-TOKEN PREDICTION (ciri khas Aeryn)
- Rule prompt: akhir setiap jawaban wajib ada prediksi kelanjutan
  '➡️ ...' — apa yang kemungkinan user tanya/butuh selanjutnya.
- Live: '➡️ Mau kubantu milih framework yang pas buat kebutuhanmu?'

Verifikasi: 427 → **432 tests green**; live kedua fitur tampil.

## V38.9b (2026-08-25) — TOCTOU guard fs_write (O_NOFOLLOW)

M16 eskalasi: celah race condition (check-then-use) di fs_write —
symlink bisa di-swap SETELAH check_path lolos, SEBELUM open() →
tulis ke file DI LUAR sandbox.

Fix: open via parent dir_fd + O_NOFOLLOW — bila komponen akhir adalah
symlink, kernel menolak (ELOOP). Verifikasi dengan simulasi swap
(monkeypatch os.open): .env asli utuh, penulisan ditolak ELOOP.
Penulisan normal + auto-create parent tetap jalan.

Verifikasi: 412 → **415 tests green**.

## V38.9 (2026-08-25) — Fine-tuning M17: math_calc DoS ditutup

Probe M17 (resource exhaustion) menemukan: `math_calc("9**9**9")`
MENGHANGKAN thread daemon >30 detik — komputasi bigint eksponensial
tanpa guard. Satu tool call = DoS pada seluruh Aeryn.

Fix berlapis di `_safe_eval`:
- Depth guard maks 20 level nesting.
- Operand guard: konstanta >10^12, eksponen >1000, hasil >10^18 → tolak.
- Semua ditolak SEBELUM komputasi (<0.01s).

Verifikasi: 408 → **412 tests green**; 9**9**9 kini ditolak instan;
2**10 tetap jalan normal.

## V39.3 (2026-08-25) — Reminder internal + Image understanding

### set_reminder (pengingat internal)
- Tool `set_reminder(note, delay_minutes)` — persist JSON, atomic pop,
  cap 100 + evict fired, rentang 10 menit s/d 7 hari.
- `_reminder_loop`: cek tiap 30 detik; jatuh tempo → dijalankan sebagai
  run kecil di session pemiliknya (laporan otomatis ke channel asal).
- Live: "ingatkan aku 2 menit lagi minum air" → reminder terpasang →
  fired 2 menit kemudian → log "[aeryn] reminder fired".

### image_understand (vision)
- Kirim URL/path gambar ke model vision Nous (ox-alpha multimodal).
- Guard: scheme/path sandbox (realpath), maks 8MB, marker sensitif.
- Symlink escape → ditolak check_path.

### Bug klasifikasi baru: reminder request dikira sosial
- "ingatkan aku 2 menit lagi" masuk jalur sosial → tools di-strip →
  Aeryn malah jawab "aku nggak bisa kirim pesan duluan".
- Fix parity daemon+generator: prefix ingatkan/remind/pengingat = bukan
  sosial; plus pengecualian riwayat (pola V37.2) supaya jawaban lama
  tidak meniru.

Verifikasi: 402 → **408 tests green**; live roundtrip reminder sukses.

## V39.2 (2026-08-25) — Tool dasar dari analisa episode + fallback map 100%

### Analisa data → 2 tool dasar
- `datetime_now`: pertanyaan waktu/tanggal berulang tanpa sumber kebenaran
  (model menebak = halusinasi tanggal). Kini: zona waktu IANA + nama hari
  Indonesia. Live: "hari apa jam berapa?" → dijawab dari tool, bukan tebakan.
- `math_calc`: kalkulasi aman via AST-whitelist (+ - * / % // **) — TANPA
  eval bebas; __import__/open/exec ditolak.

### Fallback map kini 100% (14/14 tool)
- Kontrak V39.1 tuntas: tidak ada lagi tool yang bisa error tanpa arahan.
- Test permanen menjaga: tool baru tanpa fallback map = test merah.

Verifikasi: 398 → **402 tests green**; live datetime via tool ✅.

## V39.1 (2026-08-25) — FallbackRouter: dari menolak ke mengarahkan

Filosofi baru dari Sen: memperbaiki celah terus-menerus tanpa ujung itu
salah. Setiap kegagalan tool harus DIARAHKAN ke langkah berikutnya yang
jelas — fallback tool alternatif, degradasi, atau lapor user dengan
format tertentu. Model tidak dibiarkan bengong menebak.

- `aeryn_core/fallback_router.py`: FALLBACK_MAP per-tool (rule "when"
  → directive "say"); default directive utk tool tak terdaftar.
- Wiring daemon: directive di-append ke hasil error sebelum dikirim
  balik ke model — langkah berikutnya SELALU eksplisit.
- Kunci keamanan terjaga: denial sensitif mengarahkan LAPOR + JANGAN
  bypass (bukan petunjuk menembus).

Live E2E: web_read ditolak SSRF guard → directive masuk → model langsung
melaporkan pemblokiran + menawarkan jalan keluar dalam SATU jawaban
(dulu: 3 iterasi putar-putar lalu answer=None).

Verifikasi: 391 → **398 tests green**; ALL PARITY tetap.

## V38.8 (2026-08-25) — Privacy lintas-user: episodes & sessions

Temuan M16 (cross-user privacy): fs_read bisa membaca
episodes/episodes.jsonl yang berisi goal SEMUA user Discord — user A
bisa meminta isi pertanyaan user B.

- Fix: `episodes.jsonl` masuk SECRET_BASENAMES; direktori `sessions/`
  dan `episodes/` diblokir untuk mode read (path mana pun di dalamnya).
- Live E2E: Aeryn diminta baca episode via Discord session → ditolak
  kernel → dia melapor "ditolak lapisan keamanan".

Verifikasi: 388 → **391 tests green**; ALL PARITY tetap.

## V38.7 (2026-08-25) — Fine-tuning putaran kedua: 4 celah baru

Metode generasi-2 (M10–M14) dijalankan → 4 temuan:

1. **Injection marker vs homoglyph** — deteksi injection kini konsisten
   setelah normalisasi unicode (test NFKC fullwidth).
2. **RateLimiter memory leak** — 10k session unik = 10k entri abadi.
   Fix: evict session stale saat internal dict > 1000.
3. **Audit trail tidak dilindungi** — core_memory.json.audit.jsonl bisa
   dibaca/ditimpa via fs tool (jejak harus asli!). Fix: PROTECTED_SUFFIXES
   di SecurityKernel (.audit.jsonl = tolak read & write).
4. **Reset endpoint tanpa otorisasi** — POST /session/{sid}/reset bisa
   dipanggil siapa pun untuk hapus state afektif sesi lain.
   Fix: _master_allowed() (sesi dc_*/Discord ID saja).

Verifikasi: 383 → **388 tests green**; ALL PARITY tetap; live probe
ulang semua vektor tertutup.

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
