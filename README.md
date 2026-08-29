# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, and **security-first architecture**.

![Version](https://img.shields.io/badge/version-42.0-blue)
![Tests](https://img.shields.io/badge/tests-602%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![Adaptive](https://img.shields.io/badge/adaptive-rules-success)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Security-First Architecture (NEW in V42)
- **Prompt Injection Defense**: Input sanitization, output validation, extraction detection
- **Memory Injection Defense**: Integrity verification, access audit trail
- **Tool Permission Limits**: Risk-based tool access, blast radius reduction
- **Model Routing**: Tiered model selection (60-70% cost reduction)
- **Token Monitoring**: Per-request tracking, budget enforcement, cost attribution

### Adaptive Rule Engine (V42)
- **Hot-reloadable rules** — Change behavior without restart
- **Priority-based evaluation** — Higher priority rules execute first
- **Multiple conditions**: always, contains, equals, regex, threshold
- **Multiple actions**: allow, deny, log, redirect, custom

### Authentication & Security
- JWT-based authentication with API keys
- SSO (Google OAuth, GitHub OAuth)
- Role-Based Access Control (RBAC)
- Rate limiting with SQLite fallback
- Circuit breaker pattern
- PBKDF2-SHA256 password hashing

### AI Capabilities
- Multi-model LLM support (Gemini → OpenRouter → DeepSeek fallback)
- Hybrid search (semantic + keyword)
- Proactive suggestions & pattern detection
- Advanced reasoning with multi-step Chain-of-Thought
- Episodic, temporal, and graph memory

### Rust Engine
- **VectorDB**: Cosine similarity search (10-100x faster)
- **RateLimiter**: Sliding window (microsecond precision)
- **SSE Broadcaster**: High-concurrency broadcaster
- **WebSocket Server**: Scalable WebSocket server
- **Connection Pool**: PostgreSQL connection pooling

### Hermes Integration
- **35 skills** (3 Aeryn custom + 32 Hermes shared)
- **26 scripts** (8 Aeryn custom + 18 Hermes shared)
- **3 operating modes**: Plugin, Standalone + Hermes, Standalone

### Platform
- Team workspaces with shared memory
- Plugin marketplace (publish, search, rate)
- Webhook system for external integrations
- SOC2 compliance module

### Billing & Usage
- Usage metering per event type
- Stripe integration
- Quota management per plan

### DevOps
- **CI/CD Pipeline**: GitHub Actions
- **Docker Support**: Dockerfile + docker-compose
- **Monitoring**: Metrics collector + token monitoring
- **Load Testing**: Locust-based

---

## 🏗️ Architecture

```
Aeryn/
├── aeryn_core/              ← Python (147 modules)
│   ├── auth/                ← Auth, SSO, rate limiting
│   ├── billing/             ← Billing, usage metering
│   ├── cost/                ← NEW: Token monitoring, model routing
│   ├── database/            ← VectorDB, SQLite, Neon PG
│   ├── hermes_bridge/       ← Hermes adapter (shared skills/scripts)
│   ├── memory/              ← Vault, semantic, temporal
│   ├── platform/            ← Webhooks, plugins, workspaces
│   ├── reasoning/           ← Context, reasoning style
│   ├── safety/              ← Security, guardrails
│   └── security/            ← NEW: Prompt injection, memory guard, tool permissions
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 602 tests
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

## 🧪 Testing

```bash
# All tests
./venv-proot/bin/python -m pytest tests/ -v

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:3010
```

---

## 🔒 Security

### Prompt Injection Defense
- Input sanitization for all user inputs
- System prompt separation from user data
- Output validation before execution
- Runtime content filters for adversarial patterns
- Tool permission limits (blast radius reduction)

### Memory Injection Defense
- Memory integrity verification
- Session isolation enforcement
- Memory access audit logging
- Anomaly detection for memory access patterns

### Tool Permission System
- Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
- Confirmation required for high-stakes actions
- Session-based tool access limits
- Blast radius reduction

### Cost Optimization
- Token usage tracking per request
- Cost attribution by team/feature/user
- Model routing (tiered selection)
- Budget enforcement

---

## 📊 Test Coverage

```
602 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
