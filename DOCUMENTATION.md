# 📚 Aeryn v2 — Documentation

> Comprehensive documentation for the Aeryn AI Agent platform.
> Version: 2.0 (Hybrid Rust+Python Architecture)
> Last Updated: 2026-09-02

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Rust Engine](#rust-engine)
4. [Python Logic Layer](#python-logic-layer)
5. [API Endpoints](#api-endpoints)
6. [Deployment](#deployment)
7. [Development Roadmap](#development-roadmap)

---

## Architecture Overview

Aeryn v2 is a hybrid AI agent platform with:

- **Engine (Rust)**: Performance-critical operations (vector search, hashing)
- **Logic (Python)**: Business logic, API routes, agent coordination
- **Frontend (React)**: Dashboard and chat interface

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                    apps/web/ → Vite + esbuild                │
└──────────────────────────┬──────────────────────────────────┘
                           │ /api proxy
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Server (Python)                   │
│                  apps/api/routers/main.py                    │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│  │ Engine  │ Safety  │ Memory  │Reasoning│ Agents  │       │
│  │ Router  │ Router  │ Router  │ Router  │ Router  │       │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘       │
└──────────────────────────┬──────────────────────────────────┘
                           │ C FFI (ctypes)
┌──────────────────────────▼──────────────────────────────────┐
│                    Rust Engine (aeryn-engine)                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ libaeryn_engine.so                                   │   │
│  │ - cosine_similarity                                  │   │
│  │ - euclidean_distance                                 │   │
│  │ - hash_text (SHA-256)                                │   │
│  │ - word_count                                         │   │
│  │ - find_top_k                                         │   │
│  │ - free_string                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
aeryn-core-agent/
├── aeryn-engine/                  # Rust Engine
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs                 # Core types + C API
│   │   ├── c_api.rs               # C FFI functions
│   │   ├── db.rs                  # SQLite adapter
│   │   ├── graph.rs               # Graph traversal
│   │   └── processor.rs           # File processor
│   └── target/release/
│       └── libaeryn_engine.so     # 460KB shared library
│
├── aeryn_core/                    # Python Logic Layer
│   ├── engine/                    # Engine wrappers
│   ├── agents/                    # 5 Cognitive Divisions
│   │   ├── division_1_creative/
│   │   ├── division_2_psych/
│   │   ├── division_3_reasoning/
│   │   ├── division_4_gov/
│   │   └── division_5_infra/
│   ├── auth/                      # JWT, API keys, RBAC
│   ├── database/                  # SQLite/PostgreSQL adapters
│   ├── memory/                    # Memory systems
│   │   ├── vault.py               # File-based memory
│   │   ├── episodic_memory.py     # Event-based memory
│   │   ├── graph_memory.py        # Relationship-based memory
│   │   ├── hybrid_search.py       # Combined search
│   │   ├── social_memory.py       # Person/Entity memory
│   │   ├── memory_decay.py        # Memory decay
│   │   └── semantic_recall.py     # Similarity recall
│   ├── observability/             # Tracing, metrics
│   ├── platform/                  # Integrations
│   ├── plugins/                   # Plugin system
│   ├── safety/                    # Guardian, guardrails, verification
│   └── utils/                     # Config, logger, LLM client
│
├── apps/
│   ├── api/
│   │   └── routers/
│   │       ├── main.py            # FastAPI app
│   │       ├── engine.py          # Vector/text endpoints
│   │       ├── safety.py          # Safety endpoints
│   │       ├── memory.py          # Memory endpoints
│   │       ├── reasoning.py       # Reasoning endpoints
│   │       ├── agents.py          # Agent endpoints
│   │       ├── platform_router.py # Platform endpoints
│   │       ├── dead_code_router.py# Dead code endpoints
│   │       ├── chat.py            # Chat endpoints
│   │       ├── auth.py            # Auth endpoints
│   │       ├── dashboard.py       # Dashboard endpoints
│   │       ├── plugins.py         # Plugin endpoints
│   │       ├── workspaces.py      # Workspace endpoints
│   │       ├── notifications.py   # Notification endpoints
│   │       ├── shared.py          # Shared endpoints
│   │       ├── web_routes.py      # SPA routes
│   │       ├── phase4.py          # Phase 4 endpoints
│   │       ├── admin.py           # Admin endpoints
│   │       └── tools.py           # Tool endpoints
│   └── web/                       # React frontend
│       └── index.html             # SPA entry
│
├── logs/                          # Application logs
├── ecosystem.config.cjs           # PM2 configuration
├── venv-proot/                    # Python virtual environment
└── e2e_test.py                    # E2E test suite
```

---

## Rust Engine

### Build

```bash
cd aeryn-engine
cargo build --release
# Output: target/release/libaeryn_engine.so (460KB)
```

### C API Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `cosine_similarity` | `fn(*const f32, *const f32, usize) -> f32` | Cosine similarity between two vectors |
| `euclidean_distance` | `fn(*const f32, *const f32, usize) -> f32` | Euclidean distance |
| `hash_text` | `fn(*const c_char) -> *mut c_char` | SHA-256 hash |
| `word_count` | `fn(*const c_char) -> u32` | Count words in text |
| `find_top_k` | `fn(query, query_len, vectors, num_vectors, dim, k, out_indices, out_scores) -> usize` | Batch top-k search |
| `free_string` | `fn(*mut c_char)` | Free Rust-allocated string |

### Usage from Python

```python
import ctypes
lib = ctypes.CDLL('aeryn-engine/target/release/libaeryn_engine.so')
# Use cosine_similarity, hash_text, etc.
```

---

## Python Logic Layer

### Engine Module (`aeryn_core/engine/`)

| Class | Description |
|-------|-------------|
| `VectorStore` | In-memory vector store with cosine similarity search |
| `TextSplitter` | Recursive character text splitter with overlap |
| `Tokenizer` | Word tokenizer with stopword removal |
| `Database` | SQLite adapter with connection pooling |

### Memory Module (`aeryn_core/memory/`)

| Module | Description |
|--------|-------------|
| `vault.py` | File-based Obsidian-style memory (Raw/Wiki/Projects/System/Daily/Skills layers) |
| `episodic_memory.py` | Event-based memory with hybrid recall |
| `graph_memory.py` | Graph-based memory (related_to, supersedes, depends_on, contradicts, extends, causes) |
| `hybrid_search.py` | FTS5 + vector similarity search |
| `social_memory.py` | Person/Entity social memory |
| `memory_decay.py` | Time-based memory decay |
| `semantic_recall.py` | TF-IDF semantic recall |
| `session_history.py` | Conversation session history |
| `entity_resolution.py` | Entity deduplication and resolution |
| `supersession.py` | Version control for memory |
| `memory_canary.py` | Memory integrity checking |
| `memory_consolidation.py` | Memory merging |
| `memory_curator.py` | Memory organization |
| `memory_indexer.py` | Vault indexing |
| `memory_learning.py` | Preference learning |
| `temporal_memory.py` | Time-based memory |

### Agents Module (`aeryn_core/agents/`)

| Division | Description |
|----------|-------------|
| `division_1_creative/` | Style, POV, narrative (POV Enforcer, Style Switcher) |
| `division_2_psych/` | Mental health, peace (Leaky Integrator, Mental Health Core, Peace Keeper) |
| `division_3_reasoning/` | MCTS, FOL, critique, graph (MCTS Scheduler, FOL Gate, Critique, Graph Traverser) |
| `division_4_gov/` | Constitutional compliance, requirements (Context Drift Shield, EARS Parser) |
| `division_5_infra/` | Sync, validation, consensus (Narrative Ledger Sync, Sagas Validator) |

### Safety Module (`aeryn_core/safety/`)

| Module | Description |
|--------|-------------|
| `guardian.py` | Prompt injection, dangerous content, exfiltration detection |
| `guardian_enhanced.py` | Multi-dimensional risk assessment |
| `guardrails.py` | Input/output validation with PII detection |
| `enhanced_guardrails.py` | Validator registry with pluggable validators |
| `critic_pass.py` | Response critique |
| `critic_refine.py` | Self-refine critic loop |
| `owasp_security.py` | OWASP agentic security scanning |
| `injection_sweep.py` | Vulnerability scanning |
| `verifier.py` | Answer verification |
| `verification_gate.py` | Claim checking |
| `shadow_mode.py` | Parity checking |
| `production_guard.py` | Production guards |
| `research_guard.py` | Ungrounded factual check |
| `secrets_runtime.py` | Secrets management |
| `security_hardening.py` | Path/command validation |
| `security_kernel.py` | Secure terminal |
| `sandbox.py` | Command sandbox |
| `terminal_tool.py` | Terminal tool |
| `soc2_compliance.py` | SOC2 compliance |

---

## API Endpoints

### Engine (Rust FFI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/engine/vector/{store_id}/insert` | Insert vector |
| POST | `/v1/engine/vector/{store_id}/search` | Search vectors |
| GET | `/v1/engine/vector/{store_id}/stats` | Store statistics |
| POST | `/v1/engine/text/split` | Split text into chunks |
| GET | `/v1/engine/text/tokenize` | Tokenize text |

### Safety

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/safety/guardian/check` | Guardian check |
| POST | `/v1/safety/guardian/sanitize` | Sanitize output |
| POST | `/v1/safety/guardian/enhanced/check` | Enhanced guardian |
| POST | `/v1/safety/guardrails/validate-input` | Validate input |
| POST | `/v1/safety/guardrails/validate-output` | Validate output |
| GET | `/v1/safety/guardrails/validators` | List validators |
| POST | `/v1/safety/critic/pass` | Critic pass |
| POST | `/v1/safety/critic/refine` | Critic refine |
| POST | `/v1/safety/owasp/scan` | OWASP scan |
| POST | `/v1/safety/sweep/run` | Injection sweep |
| GET | `/v1/safety/sweep/backlog` | Weakness backlog |
| POST | `/v1/safety/verify/answer` | Verify answer |
| POST | `/v1/safety/verify/claims` | Verify claims |
| POST | `/v1/safety/shadow/run` | Shadow run |
| GET | `/v1/safety/shadow/summary` | Shadow summary |
| POST | `/v1/safety/harden/validate-path` | Validate path |
| POST | `/v1/safety/harden/sanitize-command` | Sanitize command |
| POST | `/v1/safety/production/validate-payload` | Validate payload |
| GET | `/v1/safety/production/rotate-files` | Rotate files |
| POST | `/v1/safety/research/ungrounded` | Ungrounded check |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/memory/vault/write` | Write to vault |
| GET | `/v1/memory/vault/read/{filename}` | Read from vault |
| GET | `/v1/memory/vault/search` | Search vault |
| GET | `/v1/memory/vault/entries` | List entries |
| POST | `/v1/memory/episodic/record` | Record episode |
| GET | `/v1/memory/episodic/recall` | Recall episodes |
| POST | `/v1/memory/graph/node` | Add graph node |
| POST | `/v1/memory/graph/edge` | Add graph edge |
| GET | `/v1/memory/graph/neighbors/{node_id}` | Get neighbors |
| POST | `/v1/memory/temporal/store` | Store temporal |
| GET | `/v1/memory/temporal/timeline` | Get timeline |
| GET | `/v1/memory/hybrid/search` | Hybrid search |
| POST | `/v1/memory/hybrid/index` | Index content |
| GET | `/v1/memory/semantic/recall` | Semantic recall |
| POST | `/v1/memory/social/know` | Know person |
| GET | `/v1/memory/social/remember/{person_id}` | Remember person |
| POST | `/v1/memory/decay/run` | Run decay |
| GET | `/v1/memory/decay/stats` | Decay stats |
| POST | `/v1/memory/consolidate/run` | Consolidate |
| GET | `/v1/memory/consolidate/should` | Should consolidate |
| POST | `/v1/memory/curate/run` | Curate |
| POST | `/v1/memory/supersede` | Supersede |
| GET | `/v1/memory/supersede/{content_id}` | Get superseded |
| POST | `/v1/memory/canary/plant` | Plant canary |
| GET | `/v1/memory/canary/probe` | Probe canary |
| POST | `/v1/memory/session/record` | Record session |
| GET | `/v1/memory/session/history` | Session history |
| GET | `/v1/memory/session/turns` | Turn count |
| POST | `/v1/memory/entity/register` | Register entity |
| GET | `/v1/memory/entity/resolve` | Resolve entity |
| POST | `/v1/memory/enhanced/extract` | Extract entities |
| POST | `/v1/memory/enhanced/learn` | Learn preference |
| GET | `/v1/memory/enhanced/preferences/{user_id}` | Get preferences |
| POST | `/v1/memory/learn/interaction` | Learn interaction |
| GET | `/v1/memory/learn/context/{user_id}` | Get user context |

### Reasoning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/reasoning/cerewet/detect` | Detect commitment |
| POST | `/v1/reasoning/cerewet/add` | Add commitment |
| GET | `/v1/reasoning/cerewet/pending/{user_id}` | Pending commitments |
| POST | `/v1/reasoning/cerewet/settle` | Settle commitment |
| GET | `/v1/reasoning/constitutional/principles` | Constitutional principles |
| POST | `/v1/reasoning/constitutional/check` | Constitutional check |
| POST | `/v1/reasoning/context/estimate-tokens` | Estimate tokens |
| POST | `/v1/reasoning/context/trim-messages` | Trim messages |
| GET | `/v1/reasoning/context/should-summarize` | Should summarize |
| POST | `/v1/reasoning/context/classify` | Classify goal |
| POST | `/v1/reasoning/context/build` | Build context |
| POST | `/v1/reasoning/dream/synthesize` | Dream synthesize |
| GET | `/v1/reasoning/dream/insights` | Dream insights |
| GET | `/v1/reasoning/dream/summary` | Dream summary |
| GET | `/v1/reasoning/emotion/tone-directive` | Tone directive |
| POST | `/v1/reasoning/emotion/detect-mood` | Detect mood |
| POST | `/v1/reasoning/emotion/empathy-response` | Empathy response |
| POST | `/v1/reasoning/planner/create-task` | Create task |
| POST | `/v1/reasoning/planner/decompose-task` | Decompose task |
| GET | `/v1/reasoning/planner/task/{task_id}` | Get task |
| POST | `/v1/reasoning/planner/make-plan` | Make plan |
| GET | `/v1/reasoning/planner/load-plan` | Load plan |
| POST | `/v1/reasoning/proactive/create` | Create suggestion |
| GET | `/v1/reasoning/proactive/unread/{user_id}` | Unread suggestions |
| POST | `/v1/reasoning/proactive/mark-read` | Mark read |
| GET | `/v1/reasoning/proactive/daily/{user_id}` | Daily briefing |
| GET | `/v1/reasoning/proactive/patterns/{user_id}` | Patterns |
| GET | `/v1/reasoning/proactive/anomalies/{user_id}` | Anomalies |
| GET | `/v1/reasoning/reasoning-style/needs-research` | Needs research |
| GET | `/v1/reasoning/reasoning-style/next-token-hint` | Next token hint |
| POST | `/v1/reasoning/reflection/reflect` | Reflect |
| GET | `/v1/reasoning/reflection/recent-strategy` | Recent strategy |
| POST | `/v1/reasoning/reminder/set` | Set reminder |
| GET | `/v1/reasoning/reminder/due/{user_id}` | Due reminders |
| GET | `/v1/reasoning/reminder/pending-count/{user_id}` | Pending count |
| POST | `/v1/reasoning/self-improvement/record` | Record interaction |
| POST | `/v1/reasoning/self-improvement/submit-feedback` | Submit feedback |
| GET | `/v1/reasoning/self-improvement/feedback-stats/{user_id}` | Feedback stats |
| POST | `/v1/reasoning/self-improvement/analyze` | Analyze patterns |
| POST | `/v1/reasoning/self-improvement/optimize` | Optimize prompt |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/agents/divisions` | List 5 divisions |
| GET | `/v1/agents/{division}/prompt` | Get division prompt |
| POST | `/v1/agents/execute` | Execute sub-agent |
| GET | `/v1/agents/sub-agents` | List sub-agents |
| POST | `/v1/agents/middleware/enforce-budget` | Enforce budget |

### Platform

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/platform/browser/scrape` | Scrape URL |
| POST | `/v1/platform/browser/screenshot` | Screenshot URL |
| POST | `/v1/platform/browser/run-task` | Run browser task |
| POST | `/v1/platform/cloud/scan` | Scan files |
| POST | `/v1/platform/cloud/sync` | Sync files |
| POST | `/v1/platform/github/create-issue` | Create issue |
| POST | `/v1/platform/github/link-issue` | Link issue |
| GET | `/v1/platform/discord/commands` | Discord commands |
| POST | `/v1/platform/discord/register-command` | Register command |
| POST | `/v1/platform/email/triage` | Triage email |
| POST | `/v1/platform/email/generate-reply` | Generate reply |
| POST | `/v1/platform/calendar/create-event` | Create event |
| GET | `/v1/platform/calendar/events` | Get events |
| POST | `/v1/platform/mcp/create-key` | Create MCP key |
| GET | `/v1/platform/mcp/validate-key` | Validate MCP key |
| POST | `/v1/platform/multi-agent/register` | Register agent |
| GET | `/v1/platform/multi-agent/agents` | List agents |
| POST | `/v1/platform/rooms/create` | Create room |
| GET | `/v1/platform/rooms/{room_id}` | Get room |
| POST | `/v1/platform/tenants/create` | Create tenant |
| POST | `/v1/platform/tenants/add-user` | Add user |
| GET | `/v1/platform/skills/frequent-patterns` | Frequent patterns |
| POST | `/v1/platform/skills/record-action` | Record action |
| POST | `/v1/platform/skills/crystallize` | Crystallize skills |
| POST | `/v1/platform/webhooks/register` | Register webhook |
| POST | `/v1/platform/webhooks/trigger` | Trigger webhook |
| POST | `/v1/platform/sub-agent/spawn` | Spawn sub-agent |
| GET | `/v1/platform/tools/schemas` | Tool schemas |
| POST | `/v1/platform/tools/register` | Register tool |
| POST | `/v1/platform/tools/governance/evaluate` | Evaluate governance |

### Dead Code (Wired)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/dead/database/pg-check` | PG check |
| GET | `/v1/dead/database/neon/available` | Neon available |
| GET | `/v1/dead/database/semantic/stats` | Semantic stats |
| GET | `/v1/dead/database/vector/collections` | Vector collections |
| GET | `/v1/dead/mcp/server/list-tools` | MCP list tools |
| GET | `/v1/dead/mcp/client/discover` | MCP discover |
| GET | `/v1/dead/hermes/brain/digest` | Hermes brain |
| GET | `/v1/dead/hermes/hands/ask` | Hermes hands |
| GET | `/v1/dead/hermes/reflex/digest` | Hermes reflex |
| GET | `/v1/dead/hermes-plugin/skills` | Hermes skills |
| GET | `/v1/dead/hermes-plugin/is-plugin` | Is plugin |
| GET | `/v1/dead/hermes-plugin/has-hermes` | Has Hermes |
| GET | `/v1/dead/memory/core/render` | Memory render |
| GET | `/v1/dead/memory/graph/backlinks` | Memory backlinks |
| POST | `/v1/dead/memory/index` | Memory index |
| GET | `/v1/dead/multi-agent/workflow/ready` | Workflow ready |
| GET | `/v1/dead/personal/context/get` | Personal context |
| GET | `/v1/dead/personal/preferences/get` | Personal preferences |
| GET | `/v1/dead/safety/sandbox/terminal-log` | Terminal log |
| POST | `/v1/dead/safety/kernel/check-path` | Check path |
| GET | `/v1/dead/sandbox/detect` | Sandbox detect |
| GET | `/v1/dead/security/compliance/checks` | Compliance |
| GET | `/v1/dead/security/dashboard/events` | Security events |
| GET | `/v1/dead/security/memory-guard/verify` | Memory guard |
| POST | `/v1/dead/security/prompt-injection/detect` | Prompt injection |
| GET | `/v1/dead/security/tool-permissions/allowed` | Tool permissions |

---

## Deployment

### PM2 Configuration

```bash
# Start all services
pm2 start ecosystem.config.cjs

# Restart
pm2 restart aeryn-api

# Logs
pm2 logs aeryn-api

# Status
pm2 list
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `aeryn-api` | 3010 | FastAPI server |
| `aeryn-dashboard` | 3021 | Dashboard server |
| `rynnovel-api` | 3001 | Webnovel API (separate) |
| `rynnovel-web` | 5173 | Webnovel frontend (separate) |

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `AERYN_MODE` | `standalone` | Running mode |
| `AERYN_PORT` | `3010` | Server port |
| `AERYN_HOST` | `127.0.0.1` | Server host |
| `AERYN_ENV` | `proot` | Environment |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection |

---

## Development Roadmap

### Phase 1: Agent Core (1-2 weeks)
- [ ] LLM Client integration (OpenAI/Anthropic/local)
- [ ] Agent Loop (System prompt → User message → LLM → Tool call → Response)
- [ ] Tool Registry (dynamic tool registration)
- [ ] 5 Core Tools (bash, file_read, file_write, file_search, web_search)
- [ ] Chat Endpoint (`/v1/chat`)

### Phase 2: Memory & Context (1 week)
- [ ] Memory Recall (retrieve relevant memories before LLM call)
- [ ] Context Window (token-bounded conversation history)
- [ ] Memory Write (save to DB after conversation)

### Phase 3: Frontend Chat (3-5 days)
- [ ] Chat UI (React component)
- [ ] Streaming (SSE for real-time response)
- [ ] Tool Display (show tool calls in UI)

### Phase 4: Multi-Agent & Advanced (2 weeks)
- [ ] 5 Divisions (agent personalities)
- [ ] Plugin System (dynamic tool loading)
- [ ] Marketplace (plugin discovery & install)

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Python files | 339 |
| Total Python lines | ~39,892 |
| Total Rust files | 5 |
| Total Rust lines | ~1,073 |
| Total API endpoints | 200+ |
| E2E tests passing | 64/64 |
| Git commits | ~40 |
| Branch | `main` |

---

## License

MIT License — Copyright (c) 2026 Aeryn Team

---

> Generated: 2026-09-02
> Author: Hermes Agent (Nous Research)
> Version: 2.0
