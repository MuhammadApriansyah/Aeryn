# Aeryn — Dokumentasi yang Perlu Dikerjakan

> Berdasarkan analisis dari 8 sumber GitHub terbaik

---

## 📊 Ringkasan

| Kategori | Jumlah | Prioritas | Status |
|----------|--------|-----------|--------|
| **AI-Coding-Agent-Ready** | 10 files | ⭐⭐⭐⭐⭐ | ❌ Belum |
| **Pipeline & Team** | 4 files | ⭐⭐⭐⭐⭐ | ❌ Belum |
| **API & SDK** | 3 files | ⭐⭐⭐⭐ | ❌ Belum |
| **Channel Integration** | 4 files | ⭐⭐⭐⭐ | ❌ Belum |
| **Billing & Monetization** | 3 files | ⭐⭐⭐⭐ | ❌ Belum |
| **Plugin & Marketplace** | 2 files | ⭐⭐⭐⭐ | ❌ Belum |
| **Infrastructure** | 3 files | ⭐⭐⭐ | ❌ Belum |
| **Onboarding** | 2 files | ⭐⭐⭐ | ❌ Belum |
| **Troubleshooting** | 2 files | ⭐⭐⭐ | ✅ Ada |
| **TOTAL** | **33 files** | | |

---

## 📁 Daftar Dokumentasi Lengkap

### 1. AI-Coding-Agent-Ready (10 files) — ⭐⭐⭐⭐⭐

File-file ini memungkinkan AI coding agent (Claude Code, Cursor, Codex, OpenCode) memahami dan bekerja dengan codebase Aeryn secara otomatis.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `CLAUDE.md` | Quick start guide untuk Claude Code agents | SaaSPilot |
| 2 | `AGENTS.md` | OpenCode agent configuration | ECC |
| 3 | `.claude/skills/aeryn-dev.md` | Development skill definition | ECC |
| 4 | `.claude/skills/aeryn-deploy.md` | Deployment skill definition | ECC |
| 5 | `.claude/skills/aeryn-debug.md` | Debugging skill definition | ECC |
| 6 | `.cursorrules/rules.md` | Cursor IDE rules & conventions | SaaSPilot |
| 7 | `.ai-coding-checklist.md` | Checklist untuk AI coding agents | SaaSPilot |
| 8 | `prompts/add-new-feature.md` | Template prompt untuk tambah fitur | SaaSPilot |
| 9 | `prompts/create-api-endpoint.md` | Template prompt untuk buat API | SaaSPilot |
| 10 | `prompts/modify-database-schema.md` | Template prompt untuk ubah schema | SaaSPilot |

**Contoh isi CLAUDE.md:**
```markdown
# Aeryn — AI Agent Quick Start

## Project Overview
Aeryn is an AI personal assistant platform with 5 cognitive divisions,
6 memory layers, and recursive self-improvement capabilities.

## Stack
- Backend: Python 3.11+, FastAPI, PM2
- Frontend: HTML5, CSS3, Vanilla JavaScript (zero dependencies)
- Database: PostgreSQL (Neon), SQLite (local), pgvector
- Infrastructure: PM2, Docker, Redis (planned)

## Project Structure
```
aeryn-core-agent/
├── aeryn_core/          # Core system (5,600+ files)
│   ├── agents/          # 5 cognitive divisions
│   ├── adaptive/        # Self-improvement system
│   ├── memory/          # 6 memory types
│   └── ...
├── apps/
│   ├── api/             # FastAPI backend (port 3010)
│   └── web/             # SPA Dashboard
└── tests/               # 661 tests
```

## Common Commands
```bash
# Start backend
pm2 start apps/api/aeryn_api.py --name aeryn-api

# Run tests
pytest tests/ -x

# Check health
curl http://127.0.0.1:3010/health

# View logs
pm2 logs aeryn-api
```

## Key Conventions
- Backend: Python with type hints
- API: FastAPI with Pydantic models
- Frontend: Vanilla JS (no framework)
- Tests: pytest with fixtures
- Config: environment variables + .env

## Adding New Features
1. Define models in aeryn_core/
2. Create API endpoints in apps/api/
3. Add frontend components in apps/web/
4. Write tests in tests/
5. Update this CLAUDE.md

## Troubleshooting
- Port conflict: `fuser -k 3010/tcp`
- PM2 issues: `pm2 delete aeryn-api && pm2 start ...`
- Import errors: Check venv activation
```

---

### 2. Pipeline & Team (4 files) — ⭐⭐⭐⭐⭐

Dokumentasi untuk 8-phase startup pipeline dan digital team.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/pipeline/phases.md` | Definisi 8 fase pipeline | Agent Startup Skills |
| 2 | `docs/pipeline/team.md` | Digital team roles & responsibilities | Agent Startup Skills |
| 3 | `docs/pipeline/gates.md` | Approval gates per fase | Agent Startup Skills |
| 4 | `docs/pipeline/templates.md` | Project templates per stack | Agent Startup Skills |

**Contoh isi phases.md:**
```markdown
# Aeryn — 8-Phase Startup Pipeline

## Phase 1: Market Research
- **Agent**: Market Scout
- **Deliverable**: `market_brief.md`
- **Tasks**: Competitive analysis, risk assessment, target audience

## Phase 2: MVP Scoping
- **Agent**: MVP Scoper
- **Deliverable**: `mvp_scope.md`
- **Tasks**: Feature prioritization, lean v1 definition

## Phase 3: Architecture Design
- **Agent**: System Architect
- **Deliverable**: `architecture.md`
- **Tasks**: Tech stack selection, file structure, API contracts

## Phase 4: Schema Design
- **Agent**: Schema Designer
- **Deliverable**: `schema.md`
- **Tasks**: Database schema, relationships, migrations

## Phase 5: Full-Stack Coding
- **Agent**: Fullstack Coder
- **Deliverable**: Complete codebase
- **Tasks**: Implementation, API endpoints, frontend

## Phase 6: QA Testing
- **Agent**: Test Engineer
- **Deliverable**: `testing_plan.md`
- **Tasks**: Unit tests, integration tests, coverage report

## Phase 7: Security Audit
- **Agent**: Security Auditor
- **Deliverable**: `security_audit.md`
- **Tasks**: OWASP check, vulnerability scan, fixes

## Phase 8: Deployment Planning
- **Agent**: Deploy Planner
- **Deliverable**: `deploy_guide.md`
- **Tasks**: Docker, CI/CD, monitoring, launch guide
```

---

### 3. API & SDK (3 files) — ⭐⭐⭐⭐

Dokumentasi untuk API endpoints dan Python SDK.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/api/endpoints.md` | API reference lengkap | AaaS |
| 2 | `docs/api/python-sdk.md` | Python SDK documentation | AaaS |
| 3 | `docs/api/authentication.md` | Auth & security guide | AaaS |

**Contoh isi endpoints.md:**
```markdown
# Aeryn — API Reference

## Base URL
```
http://localhost:3010
```

## Authentication
All endpoints require Bearer token in Authorization header.

## Endpoints

### Health
- `GET /health` — Health check
- `GET /api/adaptive/health` — Adaptive system health

### Agents
- `GET /api/agents` — List all agents
- `POST /api/agents` — Create new agent
- `GET /api/agents/{id}` — Get agent details
- `PUT /api/agents/{id}` — Update agent
- `DELETE /api/agents/{id}` — Delete agent

### Adaptive System
- `GET /api/adaptive/errors` — Error summary
- `GET /api/adaptive/adaptations` — Adaptation summary
- `POST /api/adaptive/run-cycle` — Trigger improvement cycle

### Monitoring
- `GET /api/monitoring/sessions` — Chat sessions
- `GET /api/monitoring/history` — Conversation history
- `GET /api/monitoring/stats` — Monitoring stats
```

---

### 4. Channel Integration (4 files) — ⭐⭐⭐⭐

Dokumentasi untuk multi-channel deployment.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/channels/whatsapp.md` | WhatsApp Business API setup | Gravity |
| 2 | `docs/channels/telegram.md` | Telegram bot integration | Gravity |
| 3 | `docs/channels/slack.md` | Slack workspace integration | Gravity |
| 4 | `docs/channels/web-widget.md` | Embeddable web chat widget | Gravity |

**Contoh isi whatsapp.md:**
```markdown
# Aeryn — WhatsApp Integration

## Prerequisites
- WhatsApp Business API account
- Meta Business Verified
- Phone number for WhatsApp

## Setup
1. Create Meta Developer account
2. Set up WhatsApp Business API
3. Configure webhook URL
4. Add credentials to .env

## Environment Variables
```
WHATSAPP_API_URL=https://graph.facebook.com/v18.0/
WHATSAPP_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
```

## Architecture
```
User → WhatsApp → Webhook → Aeryn API → Agent → Response
```

## API Endpoints
- `POST /api/channels/whatsapp/webhook` — Receive messages
- `POST /api/channels/whatsapp/send` — Send messages

## Message Types Supported
- Text messages
- Images
- Documents
- Location
- Interactive buttons
```

---

### 5. Billing & Monetization (3 files) — ⭐⭐⭐⭐

Dokumentasi untuk credit-based billing dan subscription tiers.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/billing/credit-system.md` | Credit system & pricing | SaaSPilot |
| 2 | `docs/billing/subscriptions.md` | Subscription tiers & features | Gravity |
| 3 | `docs/billing/stripe-integration.md` | Stripe payment integration | SaaSPilot |

**Contoh isi credit-system.md:**
```markdown
# Aeryn — Credit-Based Billing

## Credit System
- 1 credit = 1 API call
- Credits are consumed per agent interaction
- Unused credits roll over (monthly)

## Pricing Tiers

### Free
- 1,000 credits/month
- 1 agent instance
- Web channel only
- Community support

### Pro ($49/month)
- 50,000 credits/month
- 5 agent instances
- Web + WhatsApp + Telegram
- Email support

### Enterprise ($199/month)
- 500,000 credits/month
- 25 agent instances
- All channels
- Priority support + SSO

## Credit Consumption

| Action | Credits |
|--------|---------|
| Simple query | 1 |
| Complex reasoning | 5 |
| Image generation | 10 |
| Document processing | 3 |
| Agent creation | 50 |

## API Endpoints
- `GET /api/billing/balance` — Check credit balance
- `POST /api/billing/purchase` — Purchase credits
- `GET /api/billing/history` — Transaction history
```

---

### 6. Plugin & Marketplace (2 files) — ⭐⭐⭐⭐

Dokumentasi untuk plugin development dan marketplace.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/plugins/development.md` | Plugin development guide | ECC |
| 2 | `docs/plugins/marketplace.md` | Marketplace guidelines | ECC |

**Contoh isi development.md:**
```markdown
# Aeryn — Plugin Development Guide

## Plugin Structure
```
plugins/
├── my-plugin/
│   ├── SKILL.md          # Plugin metadata
│   ├── __init__.py       # Entry point
│   ├── plugin.py         # Main plugin class
│   └── requirements.txt  # Dependencies
```

## SKILL.md Format
```yaml
---
name: my-plugin
version: 1.0.0
description: My custom plugin
author: Your Name
---

# My Plugin
Description of what this plugin does.

## Installation
1. Copy to plugins/
2. Restart Aeryn
3. Enable in dashboard

## Usage
How to use this plugin.
```

## Plugin API
- `on_load()` — Called when plugin loads
- `on_request(request)` — Called on API request
- `on_response(response)` — Called before response
- `on_error(error)` — Called on error

## Marketplace Submission
1. Test plugin locally
2. Create SKILL.md
3. Submit PR to marketplace
4. Review & approval
5. Published to marketplace
```

---

### 7. Infrastructure (3 files) — ⭐⭐⭐

Dokumentasi untuk deployment, caching, dan monitoring.

| # | File Path | Tujuan | Referensi |
|---|-----------|--------|-----------|
| 1 | `docs/infrastructure/deployment.md` | Production deployment guide | Gravity |
| 2 | `docs/infrastructure/caching.md` | Redis + LRU caching strategy | Gravity |
| 3 | `docs/infrastructure/monitoring.md` | Prometheus + Grafana setup | DeerFlow |

---

### 9. Troubleshooting (2 files) — ⭐⭐⭐

Dokumentasi troubleshooting yang sudah ada.

| # | File Path | Tujuan | Status |
|---|-----------|--------|--------|
| 1 | `docs/troubleshooting-nextjs-turbopack.md` | Next.js 16 + Turbopack Bus Error fixes | ✅ Ada |
| 2 | `docs/ui-recommendations.md` | UI development roadmap | ✅ Ada |

**Catatan:** 2 file ini sudah ada dan tinggal di-expand jika diperlukan.

---

## 📊 Summary

### By Priority

| Prioritas | Jumlah Files | Kategori |
|-----------|--------------|----------|
| ⭐⭐⭐⭐⭐ | 14 | AI-Coding-Agent-Ready + Pipeline | ❌ |
| ⭐⭐⭐⭐ | 9 | API + Channel + Billing + Plugin | ❌ |
| ⭐⭐⭐ | 5 | Infrastructure + Onboarding | ❌ |
| ✅ Selesai | 2 | Troubleshooting + UI Recommendations | ✅ |
| **TOTAL** | **33** | | |

### Implementation Timeline

| Sprint | Target | Files |
|--------|--------|-------|
| Sprint 0 | ✅ Sudah selesai | troubleshooting-nextjs-turbopack.md, ui-recommendations.md |
| Sprint 1 | V59 — Minggu 1-2 | CLAUDE.md, AGENTS.md, .claude/skills/, .cursorrules/ |
| Sprint 2 | V59 — Minggu 3-4 | .ai-coding-checklist.md, prompts/, billing docs |
| Sprint 3 | V60 — Minggu 5-8 | pipeline docs, channel docs |
| Sprint 4 | V60 — Minggu 9-12 | API docs, plugin docs, infra docs, onboarding, debug skill |
| **33 files total** | **4 sprints** | |

| Sumber | Files Diadaptasi |
|--------|------------------|
| SaaSPilot | 10 (AI-Coding-Agent-Ready) |
| Agent Startup Skills | 8 (Pipeline + Onboarding) |
| Gravity-SaaS-Agent | 8 (Channel + Billing + Infrastructure) |
| AaaS | 5 (API + Channel) |
| ECC | 4 (Plugin + Harness) |
| Hermes | 2 (Memory + Cross-platform) |
| DeerFlow | 1 (Monitoring) |
| Internal | 2 (Troubleshooting + UI) |

---

## 🗺️ Implementation Order

### Sprint 0 (Sudah Selesai ✅)
1. ✅ `docs/troubleshooting-nextjs-turbopack.md`
2. ✅ `docs/ui-recommendations.md`

### Sprint 1 (V59 ✅ — Minggu 1-2)
1. ✅ `CLAUDE.md`
2. ✅ `AGENTS.md`
3. ✅ `.claude/skills/aeryn-dev.md`
4. ✅ `.claude/skills/aeryn-development.md`
5. ✅ `.claude/skills/aeryn-testing.md`
6. ✅ `.claude/skills/aeryn-debugging.md`
7. ✅ `.cursorrules/.cursorrules.md`

### Sprint 2 (V59 ✅ — Minggu 3-4)
8. ✅ `docs/ai-coding-checklist.md`
9. ✅ `docs/prompts/system-prompts.md`
10. ✅ `docs/prompts/user-prompts.md`
11. ✅ `docs/billing/billing.md`

### Sprint 3 (V59 ✅ — Minggu 5-8)
12. ✅ `docs/pipeline/phases.md`
13. ✅ `docs/pipeline/team.md`
14. ✅ `docs/pipeline/gates.md`
15. ✅ `docs/pipeline/templates.md`
16. ✅ `docs/channels/whatsapp.md`
17. ✅ `docs/channels/discord.md`

### Sprint 4 (V59 ✅ — Minggu 9-12)
18. ✅ `docs/api/api-reference.md`
19. ✅ `docs/api/plugins.md`
20. ✅ `docs/api/infrastructure.md`
21. ✅ `docs/onboarding/onboarding.md`
22. ✅ `docs/onboarding/quickstart.md`

---

## ✅ Definition of Done

Setiap dokumentasi dianggap selesai ketika:
- [ ] File created with proper structure
- [ ] Content is accurate and up-to-date
- [ ] Examples are tested and working
- [ ] Links to related docs are correct
- [ ] Reviewed by at least one person
- [ ] Merged to main branch
- [ ] Accessible from main navigation

---

*Dokumen ini akan diperbarui seiring progress implementasi.*
*Target: Semua 31 files selesai di V59-V60.*
