# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, and Hermes integration.

![Version](https://img.shields.io/badge/version-41.1-blue)
![Tests](https://img.shields.io/badge/tests-590%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-clean-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Authentication & Security
- JWT-based authentication with API keys
- SSO (Google OAuth, GitHub OAuth)
- Role-Based Access Control (RBAC): admin, user, readonly
- Rate limiting per user/role (SQLite fallback)
- Circuit breaker pattern
- PBKDF2-SHA256 password hashing

### AI Capabilities
- Multi-model LLM support (Gemini → OpenRouter → DeepSeek fallback)
- Hybrid search (semantic + keyword)
- Semantic recall & memory consolidation
- Proactive suggestions & pattern detection
- Advanced reasoning with multi-step Chain-of-Thought
- Episodic, temporal, and graph memory

### Rust Engine (High-Performance)
- **VectorDB**: Cosine similarity search (10-100x faster than pure Python)
- **RateLimiter**: Sliding window rate limiter (DashMap-based, microsecond precision)
- **SSE Broadcaster**: High-concurrency Server-Sent Events broadcaster
- **WebSocket Server**: Scalable WebSocket server
- **Connection Pool**: PostgreSQL connection pooling

### Hermes Integration
- **35 skills** (3 Aeryn custom + 32 Hermes shared)
- **26 scripts** (8 Aeryn custom + 18 Hermes shared)
- **3 operating modes**: Plugin, Standalone + Hermes, Standalone
- Auto-detection of Hermes availability

### Platform
- Team workspaces with shared memory
- Plugin marketplace (publish, search, rate)
- Webhook system for external integrations
- Admin dashboard with user management
- SOC2 compliance module
- Data residency region selection

### Billing & Usage
- Usage metering per event type
- Stripe integration (subscriptions, payment intents)
- Quota management per plan (free/pro/enterprise)

### DevOps
- **CI/CD Pipeline**: GitHub Actions for build, test, deploy
- **Docker Support**: Dockerfile + docker-compose
- **Monitoring**: Metrics collector with SQLite storage
- **Load Testing**: Locust-based load testing

---

## 🏗️ Architecture

```
Aeryn/
├── aeryn_core/              ← Python (147 modules, business logic)
│   ├── auth/                ← Authentication, SSO, rate limiting
│   ├── billing/             ← Billing, usage metering
│   ├── database/            ← VectorDB, SQLite, Neon PG
│   ├── hermes/              ← Hermes integration (brain, hands, reflex)
│   ├── hermes_bridge/       ← Hermes adapter (shared skills/scripts)
│   ├── hermes_plugin/       ← Plugin wrapper
│   ├── memory/              ← Vault, semantic, temporal, episodic
│   ├── platform/            ← Webhooks, plugins, workspaces, integrations
│   ├── reasoning/           ← Context, reasoning style, proactive
│   ├── safety/              ← Security, guardrails, sandbox
│   └── utils/               ← Logger, config, performance, cache
├── aeryn-engine/            ← Rust (5 hot-path modules)
│   └── src/lib.rs           ← PyO3 bindings
├── plugins/aeryn-core/      ← Hermes plugin entry
├── scripts/                 ← Operational scripts
├── skills/                  ← Procedural knowledge
├── tests/                   ← 590 tests
├── docs/                    ← README + CHANGELOG
├── .github/workflows/       ← CI/CD Pipeline
├── monitoring/              ← Metrics collector
├── Dockerfile               ← Docker support
└── docker-compose.yml       ← Docker Compose
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+, Rust 1.75+ |
| API Framework | FastAPI |
| Database | SQLite (local) + PostgreSQL/Neon (cloud) |
| Vector Search | pgvector + semantic indexing |
| Authentication | JWT + API Keys |
| AI/LLM | Gemini, OpenRouter, DeepSeek (fallback chain) |
| Real-time | WebSocket + SSE |
| Task Queue | asyncio background tasks |
| Build System | uv + Maturin (PyO3) |
| CI/CD | GitHub Actions |
| Deployment | PM2, Docker |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python3 --version

# Rust toolchain
rustc --version

# PM2 (process manager)
npm install -g pm2

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone repository
git clone git@github.com:MuhammadApriansyah/Aeryn.git
cd Aeryn

# Setup Python environment with uv
uv venv venv-proot
source venv-proot/bin/activate
uv pip install -r requirements.txt

# Build Rust engine
cd aeryn-engine
maturin develop --release
cd ..
```

### Configuration

```bash
# Create .env file
cat > .env << 'EOF'
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
NEON_DATABASE_URL=your_neon_url_here
DATABASE_DIR=Personalisasi/Database
EOF
```

### Run

```bash
# Start with PM2
pm2 start ecosystem.config.js

# Or with Docker
docker-compose up -d
```

### Health Check

```bash
curl http://127.0.0.1:3010/health
```

---

## 📚 API Documentation

Interactive API docs available at:
- **Swagger UI**: `http://127.0.0.1:3010/docs`
- **ReDoc**: `http://127.0.0.1:3010/redoc`

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, get JWT token |
| POST | `/chat` | Chat with Aeryn |
| GET | `/search` | Semantic search |
| GET | `/health` | Health check |

---

## 🧪 Testing

```bash
# Run all tests
./venv-proot/bin/python -m pytest tests/ -v

# Run specific module tests
./venv-proot/bin/python -m pytest tests/test_auth/ -v

# With coverage
./venv-proot/bin/python -m pytest tests/ --cov=aeryn_core --cov-report=html

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:3010
```

---

## 🔧 Scripts

```bash
# Health check
./scripts/health_check.py

# Backup data
./scripts/backup.py

# Deploy to production
./scripts/deploy.py

# Monitor uptime
./scripts/monitor_uptime.py
```

---

## 🔒 Security

- PBKDF2-SHA256 password hashing (100k iterations)
- JWT tokens with expiration
- SQL injection prevention (parameterized queries + table sanitization)
- Command injection prevention (no shell=True)
- Input sanitization & validation
- Rate limiting per endpoint (SQLite fallback)
- CORS protection
- Audit logging
- No hardcoded credentials (all from .env)

---

## 📊 Test Coverage

```
590 tests pass
0 failures
1 warning
```

---

## 🔗 Hermes Integration

Aeryn can operate in three modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Plugin** | Running as Hermes plugin | User chat via Telegram/Discord |
| **Standalone + Hermes** | Aeryn standalone with Hermes shared resources | Development, testing |
| **Standalone** | Fully independent | Production deployment |

### Shared Resources

| Resource | Aeryn Custom | Hermes Shared | Total |
|----------|-------------|---------------|-------|
| Skills | 3 | 32 | 35 |
| Scripts | 8 | 18 | 26 |

---

## 📄 License

MIT License

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

---

*Built with ❤️ in Indonesia 🇮🇩*
