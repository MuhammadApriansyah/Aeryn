# Hermes vs Aeryn — Comparison & Evolution

> Date: 2026-08-28
> Hermes Version: Production (2024-2025)
> Aeryn Version: V40.55 (2026)

---

## 1. Positioning

| Aspect | Hermes | Aeryn |
|---|---|---|
| **Role** | Messaging Gateway + Orchestrator | Cognitive Agent + Platform |
| **User** | Sen (owner) | Sen (owner) + future: developers |
| **Access** | CLI, WhatsApp, Telegram, Discord | CLI, Telegram, Discord, REST, GraphQL |
| **Architecture** | Multi-profile gateway | Monolithic cognitive engine |
| **Deployment** | Production (PM2, systemd) | Development (PM2, proot) |
| **Maturity** | 2+ years, battle-tested | ~3 months, rapidly evolving |

---

## 2. Feature Comparison

### 2.1 Messaging & Channels

| Feature | Hermes | Aeryn | Winner |
|---|---|---|---|
| WhatsApp | ✅ Native (Baileys) | ❌ Via Hermes | Hermes |
| Telegram | ✅ Native | ✅ Bot API | Hermes |
| Discord | ✅ Native | ✅ Bot API | Hermes |
| Email | ✅ Himalaya CLI | ✅ IMAP/SMTP class | Tie |
| SMS | ✅ Via gateway | ❌ | Hermes |
| Signal | ✅ Via libsignal | ❌ | Hermes |
| Slack | ✅ Via bot | ❌ | Hermes |
| Web Dashboard | ❌ | ✅ Real-time HTML | Aeryn |

### 2.2 Intelligence

| Feature | Hermes | Aeryn | Winner |
|---|---|---|---|
| LLM Client | ✅ Multi-provider (NOUS/Gemini/Groq) | ❌ Via ModelClient | Hermes |
| Provider Fallback | ✅ Auto-rotate | ❌ Single provider | Hermes |
| OAuth Refresh | ✅ Auto-rotate agent_key | ❌ Token statis | Hermes |
| Memory | ✅ Vector + FTS5 + Graph | ✅ FTS5 + Semantic + Vault | Hermes |
| Reasoning | ✅ Tool calling (native) | ✅ Adapters + Safety Engine | Hermes |
| Multi-Agent | ✅ delegate_task (native) | ✅ A2A Protocol | Tie |
| Safety | ✅ Rate limiter, path jail | ✅ 21 validators, sandbox | Aeryn |
| Emotional | ❌ | ✅ Mood detection + empathy | Aeryn |
| Proactivity | ⚠️ Cron only | ⚠️ Dream + feedback loop | Tie |

### 2.3 Platform & Extensibility

| Feature | Hermes | Aeryn | Winner |
|---|---|---|---|
| Plugin System | ✅ skills/ directory | ✅ Install/unload lifecycle | Tie |
| Cron Jobs | ✅ Native (cronjob tool) | ⚠️ n8n workflows | Hermes |
| Webhooks | ✅ Via gateway | ✅ EventSource + WebSocket | Tie |
| MCP Server | ❌ | ✅ 14 tools exposed | Aeryn |
| GraphQL | ❌ | ✅ 12 queries + 9 mutations | Aeryn |
| SDK | ❌ | ❌ (planned Q2) | — |
| API Docs | ❌ | ❌ (planned Q2) | — |
| Plugin Marketplace | ❌ | ❌ (planned Q2) | — |

### 2.4 DevOps & Operations

| Feature | Hermes | Aeryn | Winner |
|---|---|---|---|
| Process Manager | ✅ PM2 | ✅ PM2 | Tie |
| Health Check | ✅ /health | ✅ /health + /metrics | Aeryn |
| Monitoring | ❌ | ✅ Real-time dashboard | Aeryn |
| Log Aggregation | ✅ pm2 logs | ✅ pm2 logs | Tie |
| Backup | ✅ Weekly cron | ✅ Cloud sync (incremental) | Aeryn |
| Testing | ✅ E2E + unit | ✅ 614 unit tests | Tie |
| CI/CD | ❌ | ❌ | — |
| Auto-Deploy | ❌ | ❌ | — |

### 2.5 Security

| Feature | Hermes | Aeryn | Winner |
|---|---|---|---|
| Auth | ✅ Multi-profile | ✅ JWT + sessions | Tie |
| RBAC | ✅ Profile isolation | ✅ admin/user/viewer | Tie |
| Encryption | ⚠️ Basic | ✅ At-rest + in-transit | Aeryn |
| Sandbox | ✅ Path jail | ✅ Path jail + resource limits | Aeryn |
| OWASP Coverage | ⚠️ Basic | ✅ Agentic Top 10 (21 validators) | Aeryn |
| Audit Trail | ❌ | ✅ Tamper-proof logs | Aeryn |
| Data Residency | ❌ | ❌ (planned Q3) | — |

---

## 3. Architecture Comparison

### Hermes Architecture
```
┌─────────────────────────────────────────────────────┐
│                  HERMES GATEWAY                       │
├─────────────────────────────────────────────────────┤
│  WhatsApp │ Telegram │ Discord │ Email │ Signal     │
├─────────────────────────────────────────────────────┤
│  Plugin System (skills/)                             │
├─────────────────────────────────────────────────────┤
│  Provider Router (NOUS → Gemini → Groq)             │
├─────────────────────────────────────────────────────┤
│  Tool Execution (browser, terminal, file, web)      │
├─────────────────────────────────────────────────────┤
│  Memory (Vector + FTS5 + Graph)                     │
├─────────────────────────────────────────────────────┤
│  Cron Jobs                                           │
└─────────────────────────────────────────────────────┘
```

### Aeryn Architecture (V40.55)
```
┌─────────────────────────────────────────────────────┐
│                  AERYN DAEMON :3010                  │
├─────────────────────────────────────────────────────┤
│  REST API │ GraphQL │ WebSocket │ SSE │ MCP        │
├─────────────────────────────────────────────────────┤
│  Safety Engine (21 validators + sandbox)            │
├─────────────────────────────────────────────────────┤
│  Cognitive Layer                                     │
│  ├── Context Specialization                          │
│  ├── Emotional Intelligence                          │
│  ├── Dream Synthesis                                │
│  └── Self-Improvement Loop                          │
├─────────────────────────────────────────────────────┤
│  Memory Layer                                        │
│  ├── Vault (files)                                  │
│  ├── Semantic Search (FTS5 + Vector)               │
│  ├── Entity Resolution                              │
│  ├── Temporal Memory                                │
│  └── Cross-Session Recall                           │
├─────────────────────────────────────────────────────┤
│  Integration Layer                                   │
│  ├── Telegram │ Discord │ Email │ Calendar │ GitHub │
│  ├── Browser │ Web Scraping │ Image Gen │ Video    │
│  └── Speech Recognition                             │
├─────────────────────────────────────────────────────┤
│  Enterprise (SSO, RBAC, Audit, Encryption)          │
└─────────────────────────────────────────────────────┘
```

---

## 4. Codebase Metrics

| Metric | Hermes | Aeryn | Notes |
|---|---|---|---|
| Python Files | ~50 | ~150 | Aeryn more modular |
| Lines of Code | ~8,000 | ~23,000 | Aeryn larger codebase |
| Core Modules | 12 | 18 | Aeryn has more subsystems |
| Test Coverage | ~60% | 96.3% | Aeryn better tested |
| Test Count | ~200 | 614 | Aeryn more tests |
| External Deps | ~30 | ~20 | Aeryn lighter deps |
| API Endpoints | ~10 | 50+ | Aeryn more exposed |

---

## 5. Evolution Timeline

### Aeryn Development (V39.22 → V40.55)

```
V39.22 ─── Safety Engine consolidation
  │
V39.64 ─── Web Dashboard (dark theme)
  │
V39.67 ─── n8n integration
  │
V39.68 ─── Semantic Recall (hybrid search)
  │
V39.69 ─── Context Specialization
  │
V39.70 ─── Shared DB + n8n workflows
  │
V39.76 ─── MCP Server (14 tools)
  │
V39.77 ─── Memory Learning (NER + preferences)
  │
V39.78 ─── Guardrails (input/output validation)
  │
V39.79 ─── Enhanced Sandbox (audit + isolation)
  │
V39.80 ─── Dream Synthesis
  │
V39.85 ─── MCP Production (auth + schemas)
  │
V39.90 ─── Enhanced Guardrails (21 validators)
  │
V39.95 ─── Enhanced Sandbox (network isolation)
  │
V40.1  ─── Multi-Agent (A2A Protocol)
  │
V40.2  ─── Long-Horizon Planning
  │
V40.3  ─── Self-Improvement Loop
  │
V40.6  ─── Memory Decay
  │
V40.7  ─── Entity Resolution
  │
V40.8  ─── Temporal Memory
  │
V40.9  ─── Skill Crystallization
  │
V40.11 ─── Plugin System
  │
V40.13 ─── Cloud Sync
  │
V40.16 ─── OWASP Agentic Top 10
  │
V40.20 ─── Discord Bot (5 slash commands)
  │
V40.30 ─── Constitutional AI
  │
V40.31 ─── Emotional Intelligence
  │
V40.33 ─── Voice Interface
  │
V40.34 ─── Multi-Tenant
  │
V40.35 ─── GraphQL API
  │
V40.36 ─── WebSocket Server
  │
V40.41 ─── Data Encryption
  │
V40.42 ─── CLI
  │
V40.43 ─── SSO/RBAC
  │
V40.44 ─── Full Feature Set (88 endpoints)
  │
V40.55 ─── SSE + WebSocket real-time
         + Dashboard V2 (Phase 1-2)
```

### Development Speed

| Period | Versions | Avg Versions/Week |
|---|---|---|
| V39.22 → V40.0 | 8 versions | 2/week |
| V40.0 → V40.20 | 20 versions | 5/week |
| V40.20 → V40.44 | 24 versions | 6/week |
| V40.44 → V40.55 | 11 versions | 3/week (polish phase) |

---

## 6. Gap Analysis: Aeryn vs Hermes

### 6.1 Aeryn Advantages over Hermes

| Advantage | Impact |
|---|---|
| **Better testing** (96.3% vs ~60%) | More reliable, less regressions |
| **Real-time dashboard** | Visual monitoring vs CLI only |
| **MCP Server** | Expose tools to Claude Code/Codex |
| **GraphQL** | Flexible querying vs REST only |
| **Emotional Intelligence** | Mood-aware responses |
| **Dream Synthesis** | Automatic pattern discovery |
| **Enhanced Safety** | 21 validators vs basic |
| **Audit Trail** | Tamper-proof logs |
| **WebSocket** | Real-time bidirectional |

### 6.2 Hermes Advantages over Aeryn

| Advantage | Impact |
|---|---|
| **Native messaging** | WhatsApp, Telegram, Discord integrated |
| **Multi-provider LLM** | Fallback chain (NOUS→Gemini→Groq) |
| **OAuth refresh** | Auto-rotate tokens |
| **Native tool execution** | Browser, terminal, file directly |
| **Cron jobs** | Built-in scheduler |
| **2+ years maturity** | Battle-tested in production |
| **Multi-profile** | Separate memory/tools per user |
| **Gateway role** | Connects to external messaging |

### 6.3 What Aeryn Needs to Match Hermes

| Gap | Priority | Effort |
|---|---|---|
| Native messaging integration | 🔴 High | Large |
| Multi-provider LLM fallback | 🔴 High | Medium |
| OAuth refresh | 🟡 Medium | Small |
| Native tool execution | 🔴 High | Large |
| Cron jobs (built-in) | 🟡 Medium | Small |
| Multi-profile isolation | 🟡 Medium | Medium |
| Production hardening | 🟡 Medium | Large |

---

## 7. Realistic Assessment

### Aeryn is **BETTER** at:
- API exposure (REST + GraphQL + WS + SSE)
- Testing & quality (96.3% coverage)
- Safety features (21 validators, audit, sandbox)
- Self-improvement (feedback loops, learning)
- Visual monitoring (real-time dashboard)
- Platform readiness (MCP, plugins, SDK-ready)

### Hermes is **BETTER** at:
- Messaging integration (native, reliable)
- LLM resilience (multi-provider fallback)
- Production maturity (2+ years, battle-tested)
- Native tool execution (direct, not via API)
- Multi-user isolation (profile system)
- Gateway functionality (connects everything)

### Bottom Line

> **Hermes is a production-ready gateway.**
> **Aeryn is a feature-rich cognitive platform in development.**

Aeryn has **more features on paper** but Hermes is **more reliable in production**.

For Aeryn to truly match Hermes:
1. Integrate messaging channels natively (or via Hermes)
2. Add multi-provider LLM fallback
3. Add built-in cron jobs
4. Production hardening (error recovery, monitoring)
5. Multi-profile isolation

---

## 8. Integration Strategy

### Option A: Aeryn as Hermes Plugin
```
Hermes Gateway → Aeryn Plugin (cognitive features)
                 ↓
                 Safety, Memory, Reasoning, Self-Improvement
```
**Pros:** Best of both worlds
**Cons:** Complex coupling

### Option B: Aeryn alongside Hermes
```
Hermes Gateway ←→ Aeryn API (REST/GraphQL)
```
**Pros:** Independent, can evolve separately
**Cons:** Duplicate features

### Option C: Aeryn absorbs Hermes features
```
Aeryn becomes the new gateway
```
**Pros:** Single platform
**Cons:** High effort, risky

### Recommendation: **Option A**
- Keep Hermes as gateway
- Aeryn as cognitive backend plugin
- Gradually migrate features

---

*Last updated: 2026-08-28*
*Aeryn V40.55 | Hermes Production*
