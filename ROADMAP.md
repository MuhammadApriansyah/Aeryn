# Aeryn — Development Roadmap 2025

> Approved: 2026-08-28
> Current Version: V40.55 (95 versions, 614 tests, Grade A)

---

## Executive Summary

**Aeryn** dikembangkan dalam 3 arah secara bertahap:

1. **Personal Assistant** (Q1) — Core value untuk penggunaan sehari-hari
2. **Platform** (Q2) — Expose ke developer & eksternal
3. **Enterprise** (Q3) — Team collaboration & compliance

---

## Q1 2025: Personal Assistant 🎯

### Goal
Aeryn menjadi personal assistant yang **proaktif, pintar, dan personal** — bukan cuma reactive.

### Fitur Utama

| # | Fitur | Deskripsi | Status |
|---|---|---|---|
| 1 | **Proactive Engine** | Suggestion/reminder tanpa ditanya | ❌ Planned |
| 2 | **Habit Learning** | Belajar rutinitas & preferensi | ❌ Planned |
| 3 | **Auto-Task Creation** | Dari percapan → task otomatis | ❌ Planned |
| 4 | **Voice Command** | "Hey Aeryn..." via Telegram/Discord | ❌ Planned |
| 5 | **Personalized Greeting** | Berdasarkan mood, waktu, konteks | ❌ Planned |
| 6 | **Mood-Aware Response** | Adaptasi tone berdasarkan mood | ✅ V40.31 |
| 7 | **Context Specialization** | Dynamic context per goal type | ✅ V40.69 |
| 8 | **Dream Synthesis** | Pattern discovery dari memory | ✅ V40.80 |
| 9 | **Self-Improvement** | Feedback loop & optimization | ✅ V40.3 |
| 10 | **Preference Learning** | Confidence scoring + decay | ✅ V40.81 |

### Architecture Additions

```
proactive_engine.py    — Trigger detection, suggestion generation
habit_tracker.py       — Pattern recognition, routine learning
voice_command.py       — Voice input/output orchestration
auto_task.py           — Natural language → task decomposition
personalization.py     — User profile, preferences, mood tracking
```

### Milestones

| Week | Deliverable |
|---|---|
| W1 | Proactive Engine v1 (time-based triggers) |
| W2 | Habit Learning v1 (basic pattern detection) |
| W3 | Auto-Task Creation (NL → tasks) |
| W4 | Voice Command v1 (Telegram voice notes) |
| W5 | Personalized Greeting (mood + context) |
| W6 | Integration testing + polish |

---

## Q2 2025: Platform 🚀

### Goal
Aeryn bisa diakses oleh **developer lain** via API yang reliable dan mudah.

### Fitur Utama

| # | Fitur | Deskripsi | Status |
|---|---|---|---|
| 1 | **Public API Docs** | Swagger/Redoc interaktif | ❌ Planned |
| 2 | **API Key Management** | Per-user key, rate limit, quota | ❌ Planned |
| 3 | **SDK Python** | `pip install aeryn-sdk` | ❌ Planned |
| 4 | **SDK TypeScript** | `npm install aeryn-sdk` | ❌ Planned |
| 5 | **Plugin Marketplace** | Share/load plugins publik | ❌ Planned |
| 6 | **Webhook System** | Push notifications ke external | ❌ Planned |
| 7 | **GraphQL API** | Flexible querying | ✅ V40.35 |
| 8 | **REST API** | Full CRUD endpoints | ✅ V40.0+ |
| 9 | **MCP Server** | Model Context Protocol | ✅ V40.76 |
| 10 | **Plugin System** | Install/unload lifecycle | ✅ V40.11 |

### Architecture Additions

```
api_gateway/
  ├── auth.py            — API key validation, OAuth2
  ├── rate_limiter.py    — Token bucket, per-key quotas
  ├── docs.py            — Swagger/Redoc generation
  └── webhooks.py        — Webhook registration, delivery

sdk/
  ├── python/
  │   ├── aeryn/
  │   │   ├── client.py
  │   │   ├── types.py
  │   │   └── async_client.py
  │   └── setup.py
  │
  └── typescript/
      ├── src/
      │   ├── client.ts
      │   ├── types.ts
      │   └── index.ts
      └── package.json

marketplace/
  ├── registry.py        — Plugin registry
  ├── validator.py       — Plugin validation
  └── publisher.py       — Publish workflow
```

### Milestones

| Week | Deliverable |
|---|---|
| W1 | API Key Management + Auth |
| W2 | Public API Docs (Swagger) |
| W3 | SDK Python v1 |
| W4 | SDK TypeScript v1 |
| W5 | Plugin MVP |
| W6 | Webhook System v1 |

---

## Q3 2025: Enterprise 🏢

### Goal
Aeryn siap untuk **team dan organisasi** dengan security & compliance.

### Fitur Utama

| # | Fitur | Deskripsi | Status |
|---|---|---|---|
| 1 | **Team Workspaces** | Shared memory per team | ❌ Planned |
| 2 | **Data Residency** | Pilih region (SG, US, EU) | ❌ Planned |
| 3 | **SSO Providers** | Google, GitHub, SAML | ❌ Planned |
| 4 | **SOC2 Compliance** | Audit log, data retention | ❌ Planned |
| 5 | **Admin Dashboard** | User management, billing | ❌ Planned |
| 6 | **SSO/Auth** | JWT + sessions | ✅ V40.43 |
| 7 | **RBAC** | admin/user/viewer roles | ✅ V40.43 |
| 8 | **Audit Trail** | Tamper-proof logs | ✅ V39.95 |
| 9 | **Data Encryption** | At-rest + in-transit | ✅ V40.41 |
| 10 | **Sandbox** | Path jail + resource limits | ✅ V39.95 |

### Architecture Additions

```
enterprise/
  ├── workspaces.py      — Team workspace management
  ├── sso.py             — SSO provider integration
  ├── compliance.py      — SOC2, GDPR helpers
  ├── admin.py           — Admin dashboard API
  └── billing.py         — Usage tracking, invoicing

infrastructure/
  ├── multi-region/      — Geo-distribution
  ├── encryption/        — Key management
  └── audit/             — Immutable audit logs
```

### Milestones

| Week | Deliverable |
|---|---|
| W1 | Team Workspaces v1 |
| W2 | SSO Providers (Google, GitHub) |
| W3 | Data Residency (configurable) |
| W4 | Admin Dashboard v1 |
| W5 | SOC2 Compliance Docs |
| W6 | Security Audit + Pen Test |

---

## Current Capabilities (V40.55)

### Intelligence & Reasoning
- ✅ Constitutional AI (7 ethical principles)
- ✅ Emotional Intelligence (mood tracking + empathy)
- ✅ Multimodal Input (OCR, image, audio, video, PDF)
- ✅ Voice Interface (STT + TTS)
- ✅ Dream Synthesis (pattern discovery)
- ✅ Context Specialization (dynamic per goal)
- ✅ Self-Improvement (feedback loop)
- ✅ Memory Decay (confidence reduction)

### Memory & Knowledge
- ✅ Vault (Obsidian-style, 429+ entries)
- ✅ Social Memory (facts + preferences)
- ✅ Hybrid Search (FTS5 + semantic vector)
- ✅ Entity Resolution (fuzzy merge)
- ✅ Temporal Memory (time-based queries)
- ✅ Cross-Session Recall
- ✅ Memory Graph (entity relationships)

### Task & Planning
- ✅ Task Queue (CRUD + priority + progress)
- ✅ Long-Horizon Planning (checkpoint/resume)
- ✅ Multi-Agent Orchestration (A2A protocol)
- ✅ Reminders (schedule + notification)
- ✅ Daily Reflection (auto-logging)

### Integrations
- ✅ Telegram Bot (3 commands)
- ✅ Discord Bot (5 slash commands)
- ✅ Email Agent (auto-triage + reply)
- ✅ Calendar (Google/Outlook sync)
- ✅ GitHub (Issues, PR, CI/CD)
- ✅ Browser Automation (Playwright/Selenium)
- ✅ Web Scraping (HTML → markdown/text)
- ✅ Image Generation (DALL-E)
- ✅ Video Analysis (keyframe extraction)
- ✅ Speech Recognition (Whisper)

### Platform
- ✅ REST API (50+ endpoints)
- ✅ GraphQL API (12 queries + 9 mutations)
- ✅ MCP Server (14 tools exposed)
- ✅ WebSocket (real-time commands)
- ✅ SSE (real-time streaming)
- ✅ Plugin System (install/unload)
- ✅ API Gateway (rate limit + auth + cache)

### Safety & Security
- ✅ OWASP Agentic Top 10 (21 validators)
- ✅ Input/Output Guardrails
- ✅ Data Encryption (at-rest)
- ✅ Audit Trail (sandbox logs)
- ✅ Secure Sandbox (path jail + limits)
- ✅ Rate Limiter (token bucket)
- ✅ Circuit Breaker (fail-fast)

### Enterprise
- ✅ SSO/Auth (JWT + sessions)
- ✅ RBAC (admin/user/viewer)
- ✅ Multi-Tenant (per-user isolation)
- ✅ Cloud Sync (incremental backup/restore)
- ✅ SLA Monitoring (uptime + latency)

### Monitoring & DevOps
- ✅ CLI (terminal commands)
- ✅ Dashboard (real-time monitoring)
- ✅ Testing (614 tests, 96.3% coverage)
- ✅ Tracing (Prometheus metrics)
- ✅ Cost Tracking (token usage + billing)
- ✅ Maintenance Automation (cron + scripts)

---

## Metrics & KPIs

| Metric | Current | Q1 Target | Q2 Target | Q3 Target |
|---|---|---|---|---|
| Versions | 95 | 110 | 130 | 150 |
| Tests | 614 | 700 | 800 | 900 |
| Features | 50+ | 60+ | 75+ | 90+ |
| API Endpoints | 50+ | 60+ | 80+ | 100+ |
| Uptime | ~99% | 99.5% | 99.9% | 99.95% |
| Response Time | <200ms | <150ms | <100ms | <50ms |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ (ARM64 proot) |
| API | FastAPI + Uvicorn |
| Database | SQLite (FTS5) + Vector Store |
| Frontend | Vanilla JS + Canvas |
| Realtime | SSE + WebSocket |
| Auth | JWT + bcrypt |
| Deployment | PM2 + nginx (future) |

---

## Contributing

1. Fork → Branch → PR
2. Tests required (`pytest tests/ -q`)
3. Lint clean (`python -m py_compile`)
4. Document new features in `FEATURE_ROADMAP.md`

---

## License

Private — Sen's personal project.

---

*Last updated: 2026-08-28*
