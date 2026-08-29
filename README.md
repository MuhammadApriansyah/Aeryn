# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, and **Fullstack AI Engineer mode**.

![Version](https://img.shields.io/badge/version-46.0-blue)
![Tests](https://img.shields.io/badge/tests-630%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![MCP](https://img.shields.io/badge/mcp-protocol-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Fullstack AI Engineer (NEW in V46)
- **Fullstack CLI**: Complete CLI for full-stack development (`new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`)
- **Realistic Templates**: React + Fastify + SQLite with auth, CRUD, file upload
- **Migration System**: Database migrations with rollback support
- **Hot Reload**: Development workflow with live reload
- **Multi-target Deploy**: PM2, Docker, Vercel support

### Native Sandbox (V45)
- **Conditional Security**: Auto-detect environment → use best available isolation level
- **Directed Fallback**: Graceful degradation if higher levels fail
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full
- **Zero Dependencies**: Works without Docker, Bubblewrap, or root

### MCP Protocol (V43)
- **MCP Server**: Serve tools, resources, prompts to external MCP clients
- **MCP Client**: Connect to external MCP servers and invoke tools

### Multi-Agent Orchestration (V43)
- **Workflow Engine**: Coordinate multiple agents
- **Task Management**: Priority-based task execution

### Security-First Architecture (V42)
- **Prompt Injection Defense**: Input sanitization, output validation
- **Memory Injection Defense**: Integrity verification, access audit
- **Tool Permission Limits**: Risk-based tool access
- **Model Routing**: Tiered model selection (60-70% cost reduction)
- **Token Monitoring**: Per-request tracking, budget enforcement

### Adaptive Rule Engine (V42)
- **Hot-reloadable rules** — Change behavior without restart
- **Priority-based evaluation** — Higher priority rules execute first

---

## 🏗️ Architecture

```
Aeryn/
├── aeryn_core/              ← Python (175+ modules)
│   ├── auth/                ← Auth, SSO, rate limiting
│   ├── billing/             ← Billing, usage metering
│   ├── cost/                ← Token monitoring, model routing
│   ├── database/            ← VectorDB, SQLite, Neon PG
│   ├── fullstack/           ← NEW: Fullstack AI Engineer mode
│   │   ├── cli/             ← Fullstack CLI (new, dev, migrate, test, build, deploy)
│   │   ├── templates/       ← Project templates (React, Vue, Fastify)
│   │   ├── migration/       ← Database migration system
│   │   ├── planner.py       ← Project planning & architecture
│   │   ├── engine.py        ← Fullstack orchestrator
│   │   ├── frontend.py      ← Frontend generator
│   │   ├── backend.py       ← Backend generator
│   │   ├── database.py      ← Database designer
│   │   ├── api_gen.py       ← API generator
│   │   ├── test_gen.py      ← Test generator
│   │   └── deploy.py        ← Deploy manager
│   ├── hermes_bridge/       ← Hermes adapter
│   ├── infra/               ← Agent templates + CLI
│   ├── integrations/        ← Integration SDK
│   ├── mcp/                 ← MCP server + client
│   ├── memory/              ← Vault, semantic, temporal
│   ├── multi_agent/         ← Multi-Agent orchestrator
│   ├── personal/            ← Proactive engine + personalization
│   ├── platform/            ← Webhooks, plugins, workspaces
│   ├── reasoning/           ← Context, reasoning style
│   ├── safety/              ← Security, guardrails
│   ├── sandbox/             ← Native sandbox (4 levels)
│   └── security/            ← Prompt injection, memory guard, dashboard
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 630 tests
├── .github/workflows/       ← CI/CD Pipeline
├── Dockerfile + compose     ← Docker support
└── monitoring/              ← Metrics collector
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+, Rust 1.75+ |
| API Framework | FastAPI |
| Database | SQLite (local) + PostgreSQL/Neon (cloud) |
| Authentication | JWT + API Keys |
| AI/LLM | Gemini, OpenRouter, DeepSeek (fallback) |
| Protocol | MCP (Model Context Protocol) |
| Build System | uv + Maturin (PyO3) |
| CI/CD | GitHub Actions |
| Deployment | PM2, Docker |

---

## 🚀 Quick Start

```bash
# Clone
git clone git@github.com:MuhammadApriansyah/Aeryn.git
cd Aeryn

# Setup Python
uv venv venv-proot
source venv-proot/bin/activate
uv pip install -r requirements.txt

# Build Rust engine
cd aeryn-engine && maturin develop --release && cd ..

# Configure
cat > .env << 'EOF'
GEMINI_API_KEY=your_key_here
DATABASE_DIR=Personalisasi/Database
EOF

# Run
pm2 start ecosystem.config.js
# OR
docker-compose up -d

# Health check
curl http://127.0.0.1:3010/health
```

---

## 📚 Fullstack AI Engineer

### CLI Commands

```bash
aeryn new my-app --template react      # Create project
aeryn dev --port 3010                  # Start dev server
aeryn db:migrate                       # Run migrations
aeryn db:seed                          # Seed database
aeryn test --watch --coverage          # Run tests
aeryn build --target node              # Build production
aeryn deploy --target pm2              # Deploy
```

### Project Templates

| Template | Frontend | Backend | Database |
|----------|----------|---------|----------|
| `react` | React + Vite | Fastify | SQLite |
| `vue` | Vue 3 + Vite | Fastify | SQLite |

### Generated Project Structure

```
my-app/
├── src/
│   ├── server.ts          # Fastify server
│   ├── routes/
│   │   ├── auth.ts        # Auth routes
│   │   └── tasks.ts       # Task CRUD routes
│   ├── database.ts        # SQLite connection
│   └── utils/
│       └── validation.ts  # Input validation
├── database/
│   ├── schema_0.sql       # User table
│   └── schema_1.sql       # Task table
├── migrations/
│   ├── 001_init.sql       # Initial schema
│   └── 001_init.rollback.sql
├── seeds/
│   └── init.sql           # Seed data
├── tests/
│   ├── unit.test.ts       # Unit tests
│   └── integration.test.ts # Integration tests
├── ecosystem.config.js    # PM2 config
├── Dockerfile             # Docker image
└── docker-compose.yml     # Docker compose
```

---

## 🧪 Testing

```bash
# All tests
./venv-proot/bin/python -m pytest tests/ -v

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:3010
```

---

## 📊 Test Coverage

```
630 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
