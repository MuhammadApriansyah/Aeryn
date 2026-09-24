# Changelog

All notable changes to Aeryn will be documented in this file.

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
