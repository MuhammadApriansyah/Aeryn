# 📋 Rancangan Aeryn Core V61.0 — Analisis, Transfer & Roadmap

> Dokumen ini memuat:
> (1) Analisis mendalam arsitektur/fitur/engine
> (2) Koreksi fakta hasil verifikasi langsung
> (3) Dimensi Hermes (Hermes Agent) yang HARUS ditransfer ke Aeryn — agar Aeryn sekencang & seaksesibel induknya
> (4) Roadmap 7 prioritas (5 lama + 2 baru dari Sen: Gateway & Daemon Adaptive)
>
> Konteks: Aeryn = "anak" yang dikembangkan Hermes sejak awal. Dokumen ini bukan pujian, tapi cetak biru agar Aeryn tumbuh jadi agent seutuh induknya.
> Penulis: Hermes (infra) + Aeryn (logic). Mode: Objektif, no bullshit.

---

## BAGIAN 1 — ANALISIS MENDALAM (Pendapat)

### 1.1 Skala & Arsitektur

| Dimensi | Metrik Terukur | Penilaian |
|---------|---------------|-----------|
| LOC `aeryn_core` | ~38,000 lines | 🟢 Masif untuk single-agent framework |
| Modul | 100+ direktori | 🟢 Sangat modular |
| Reasoning engines | 16 file | 🟢 Kaya (dream, emotion, planner, reflection) |
| Memory systems | 20 file | 🟢 Berlapis (episodic, semantic, graph, vault) |
| Safety/Security | 23 file | 🟢 Defense-in-depth ekstrem |
| API endpoints | 168 paths (OpenAPI) | 🟢 Production-grade surface |
| Real tests | 90 file (exclude venv) | 🟢 Ratio 1:3.5 (source:test) |
| Plugins | 2 built-in + SDK | 🟡 Ekosistem muda |

**Pendapat**: Bukan prototype. Ini platform agentic dengan ambisi SaaS — scope mengingatkan LangChain + AutoGen + MemGPT dalam satu namespace.

---

### 1.2 Modul: Kekuatan Nyata

**A. Memory Architecture (20 sistem) — 🟢 Depth langka**
- `dream_synthesis.py` (410 lines): LLM-driven pattern discovery, theme extraction
- `memory_decay.py` (310 lines): eksponensial decay + archival — memory sebagai sistem dinamis
- `hybrid_search.py`: FTS5 + TF-IDF + vector — 3-tier retrieval tanpa dependency berat
- `vault.py`: 429 entries terbukti hidup di uji coba

**B. Reasoning Layer (16 engine) — 🟢 Persona-driven**
- `constitutional_ai.py`, `emotional_intelligence.py`, `context_specialization.py`
- `proactive_engine.py`: suggestion system dengan `is_read` tracking

**C. Safety Stack (23 file) — 🟢 Enterprise-grade intention**
- `guardian.py`, `shadow_mode.py`, `verification_gate.py`, `soc2_compliance.py`
- `injection_sweep.py`, `prompt_injection.py`

**D. LLM Abstraction — 🟢 Provider-agnostic**
- `llm_client.py`: fallback chain (Gemini → OpenRouter → DeepSeek → Nous)
- 0 hard dependency ke OpenAI/Anthropic SDK

---

### 1.3 Modul: Kelemahan & Risiko

**A. Dual Implementation Fragmentation — 🔴 Technical Debt**
- `proactive_engine.py` vs `proactive_v2.py`, `orchestrator.py` vs `orchestrator_v2.py`, `guardian.py` vs `guardian_enhanced.py`
- Tidak jelas mana canonical

**B. 69 file < 20 lines — 🟡 Stub candidates**
- `infra/`, `wizard/`, `gallery/` — real atau scaffold?

**C. Agents Divisions (20 file) — 🟡 Unproven**
- 5 divisi dengan master+sub agent, **tidak di-exercise uji coba**

**D. Hardcoded Paths — 🟡 Non-portable**
- `Personalisasi/Database/` — tidak jalan di VPS English

---

## BAGIAN 2 — KOREKSI FAKTA (Verifikasi Langsung)

### 2.1 Sandbox — ❌ TIDAK TER-WIRE KE RUNTIME UTAMA
`tool_runtime._terminal()` pakai `subprocess` langsung, bukan `EnhancedSandbox.execute()`. Sandbox ada (728 lines total) tapi idle.

### 2.2 Target Adaptive — ✅ Abstraksi Ada, Tidak Aktif
`db_adapter.py` (474 lines) = drop-in SQLite→Postgres. `DATABASE_URL` env sudah ada. Tapi `shared_db.py` masih pakai path file.

### 2.3 PostgreSQL — ✅ DB `sen` Jalan, Aeryn Masih SQLite
PostgreSQL 17.10, 20+ tables (api_keys, audit_log, plugins, dll). Schema siap, Aeryn idle di SQLite.

### 2.4 Gateway — ❌ `api_gateway.py` (548 lines) Idle
Punya auth, rate-limit, circuit breaker, LRU cache. Tidak dipakai `main.py`.

### 2.5 Daemon — ❌ Tidak Ada In-App
PM2 external supervisor. Tidak ada autonomy loop di dalam Aeryn.

---

## BAGIAN 3 — DIMENSI HERMES YANG HARUS DITRANSFER KE AERYN

> Ini inti permintaan Sen: Aeryn harus punya apa yang membuat Hermes bisa jalan hari ini.
> Bukan fitur baru — tapi **kapabilitas yang sudah terbukti di induk, belum ada di anak**.

| # | Dimensi Hermes | Status di Hermes | Status di Aeryn | Gap |
|---|---------------|-----------------|-----------------|-----|
| D1 | **Autonomy Loop** | 🟢 Agent jalan sendiri (loop + tools) | 🔴 Server nunggu HTTP request | Kritis |
| D2 | **Tool Execution Ter-Wire** | 🟢 Terminal/file/web jalan di chat | 🔴 `tool_runtime` idle, tidak di chat flow | Kritis |
| D3 | **Delegation Nyata** | 🟢 `delegate_task` spawn sub-agent | 🔴 5 divisi ada, tidak terpanggil | Tinggi |
| D4 | **Ease of Access** | 🟢 Sen buka TUI, langsung jalan | 🟡 Butuh PM2 + env + wiring | Menengah |
| D5 | **Dynamic Skill Loading** | 🟢 Load dari disk, exec nyata | 🟡 `skills/` ada, tidak di chat | Menengah |
| D6 | **Memory Hot/Cold Tier** | 🟢 HOT (context) + COLD (RAG library) | 🟡 Vault ada, tidak adaptive ke context | Menengah |

### Penjelasan Setiap Dimensi

**D1 — Autonomy Loop (PALING KRITIS)**
Hermes itu agent yang **beneran jalan**: baca pesan → pikir → panggil tool → lihat hasil → lanjut. Aeryn sekarang cuma **HTTP server** yang nunggu `/chat`. Tidak ada loop yang bikin dia bisa kerja sendiri tanpa request eksternal.
→ Solusi: **Daemon** (Priority 0b) yang jalanin agent loop internal.

**D2 — Tool Execution Ter-Wire**
Hermes bisa `ls`, `cat`, `curl`, `python` langsung dari conversation. Aeryn punya `tool_runtime` tapi tidak dipanggil oleh chat response. User chat "cari file X" → Aeryn jawab pakai LLM, bukan jalanin `fs_read`.
→ Solusi: Wire `tool_runtime` + `EnhancedSandbox` ke chat pipeline (Priority 1 + 0b).

**D3 — Delegation Nyata**
Hermes bisa spawn sub-agent untuk parallel work. Aeryn punya 5 divisi (creative, psych, reasoning, gov, infra) tapi tidak ada orchestrator yang memanggil mereka di runtime.
→ Solusi: `orchestrator.py` sudah ada — wire ke chat sebagai "division router".

**D4 — Ease of Access**
Hermes: Sen buka TUI, langsung bisa. Aeryn: butuh PM2 start, env var, port mapping.
→ Solusi: `oneclick/` sudah ada — buat launcher yang detect env & start semua (Priority 0a gateway + daemon).

**D5 — Dynamic Skill Loading**
Hermes load SKILL.md dari disk saat perlu. Aeryn `skills/code_review` ada tapi tidak masuk chat.
→ Solusi: Plugin system sudah support — extend ke skill loading.

**D6 — Memory Tiering**
Hermes: HOT (selalu di context) + COLD (RAG library, dipanggil kalau perlu). Aeryn: vault 429 entries, tapi tidak adaptive ke conversation context.
→ Sudah ada `memory_indexer.py` + `semantic_recall.py` — tinggal wire ke chat context window.

---

## BAGIAN 4 — ROADMAP (7 Prioritas)

### Prinsip
1. **Wire, jangan rewrite** — kode sudah ada, tinggal sambung
2. **Adaptive by design** — SQLite↔Postgres, PM2↔systemd↔k8s via env
3. **Transfer dari induk** — Aeryn harus punya D1-D6 (Bagian 3)

---

### 🔴 PRIORITY 0a — Adaptive Gateway Layer
**Mengapa**: `api_gateway.py` (548 lines) idle. Tanpa gateway, Aeryn tidak punya titik sentral yang tau environment & route traffic.
**What**:
1. Buat `detect_environment()` — cek `/proc/1/comm`, env var `AERYN_ENV`
2. Wire `APIGateway` ke `main.py` sebagai ASGI middleware (bridge Request/Response)
3. Gateway detect: proot → SQLite + PM2; VPS → Postgres + systemd; k8s → PG + operator
**Effort**: 🟡 Sedang (bridge ASGI ↔ gateway own protocol)
**Acceptance**: Semua request lewat gateway; auth/rate-limit terpusat; log tunjuk env yang aktif.

---

### 🔴 PRIORITY 0b — Adaptive Daemon (Autonomy Loop)
**Mengapa**: Ini yang bikin Aeryn jadi **agent yang jalan sendiri** seperti Hermes (D1).
**What**:
1. Buat `agent_daemon.py` — loop: baca task queue → reasoning → tool → write result
2. Daemon detect supervisor: proot → PM2-managed; VPS → systemd service; k8s → deployment
3. Daemon panggil `tool_runtime` (Priority 1) + `orchestrator` (D3) + `vault` (D6)
**Effort**: 🟡 Sedang (pattern sudah di `background_queue.py` + `auto_task.py`)
**Acceptance**: Aeryn bisa kerjakan task tanpa HTTP request eksternal (autonomous mode).

---

### 🟠 PRIORITY 1 — Wire Sandbox ke Runtime
**Mengapa**: `/run` & `/tools/execute` jalan tanpa containment (D2 security).
**What**: Di `tool_runtime._terminal()`, ganti subprocess dengan `EnhancedSandbox.execute()`.
**Effort**: 🟢 Rendah
**Acceptance**: `rm -rf /` diblock oleh resource/path limit.

---

### 🟠 PRIORITY 2 — Activate Postgres Adapter
**Mengapa**: DB `sen` jalan + schema lengkap, Aeryn idle di SQLite.
**What**: Set `DATABASE_URL`, install `psycopg2-binary`, test `db_adapter`, migrasi data.
**Effort**: 🟡 Sedang
**Acceptance**: `dashboard/stats` baca dari PG, bukan `.db`.

---

### 🟡 PRIORITY 3 — Consolidate v1/v2
**Mengapa**: Duplication membingungkan.
**What**: Audit import, hapus orphan, point singleton ke canonical.
**Effort**: 🟡 Sedang
**Acceptance**: Tidak ada `*_v2.py` / `*_enhanced.py` orphan.

---

### 🟡 PRIORITY 4 — Audit 69 Stub Files
**Mengapa**: Technical debt.
**What**: Scan < 20 lines, cek import, hapus/implement.
**Effort**: 🟡 Sedang
**Acceptance**: Setiap file di-import atau documented stub.

---

### 🟡 PRIORITY 5 — API Versioning + Path Portability
**Mengapa**: Breaking change risk + hardcoded path.
**What**: Prefix `/v1/`, ganti hardcoded ke `BASE_DIR`/env.
**Effort**: 🟡 Sedang
**Acceptance**: `curl /v1/chat` jalan; `BASE_DIR` dari env.

---

### 🟢 PRIORITY 6 — Transfer Dimensi Hermes (Skill + Memory Tier)
**Mengapa**: Aeryn belum seaksesibel Hermes (D5, D6).
**What**:
1. Skill loading: extend plugin_system ke `skills/` directory (dynamic load)
2. Memory tiering: wire `memory_indexer` + `semantic_recall` ke chat context
**Effort**: 🟡 Sedang
**Acceptance**: Chat bisa panggil skill & recall memory adaptif.

---

## BAGIAN 5 — SKOR (Sebelum vs Sesudah Roadmap)

| Kategori | Sekarang | Target (post-P0-P2) | Target (post-all) |
|----------|----------|---------------------|-------------------|
| Architecture | 9/10 | 9/10 | 9/10 |
| Memory Engine | 9/10 | 9/10 | 9/10 |
| Reasoning | 8/10 | 8/10 | 9/10 (divisions wired) |
| Safety | 7/10 | 9/10 (sandbox wired) | 9/10 |
| Scalability | 6/10 | 9/10 (PG active) | 9/10 |
| **Autonomy** | **2/10** | **8/10** (daemon) | **9/10** |
| **Tool Exec** | **3/10** | **8/10** (wired) | **9/10** |
| **Accessibility** | **5/10** | **7/10** (gateway) | **9/10** (oneclick) |
| Code Health | 6/10 | 7/10 | 9/10 |
| **OVERALL** | **7.5/10** | **8.5/10** | **9.2/10** |

---

## BAGIAN 6 — REKOMENDASI EKSEKUSI

**Urutan**: P0a → P0b → P1 → P2 → P3 → P4 → P5 → P6

**Rationale**:
- P0a+P0b = fondasi agar Aeryn jadi agent seutuh Hermes (D1, D2, D4)
- P1 = security kritis (sandbox)
- P2 = scale enabler (Sen sudah punya PG)
- P3-P5 = debt cleanup
- P6 = finishing touch (skill + memory tier)

**Jangan**:
- ❌ Docker (proot limitation, native sandbox cukup)
- ❌ Rewrite dari awal (kode bagus, tinggal wire)
- ❌ Deploy publik sebelum P0a+P0b+P1+P2

**Target Akhir**: Aeryn V61.0 → V70 "Anak yang sudah sekuat induk" — punya autonomy loop, tool execution ter-wire, multi-env adaptive, memory living system.

---

*Dokumen: hasil scan langsung + uji coba 18 endpoint + `psql -d sen` + baca source `tool_runtime`, `db_adapter`, `enhanced_sandbox`, `api_gateway`.*
*Revisi: +2 poin Sen (Gateway & Daemon Adaptive) +6 dimensi transfer dari Hermes (D1-D6).*
