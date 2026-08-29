# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, and enterprise features.

![Version](https://img.shields.io/badge/version-41.0-blue)
![Tests](https://img.shields.io/badge/tests-597%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-clean-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Authentication & Security
- JWT-based authentication with API keys
- Multi-factor authentication (MFA)
- SSO (Google OAuth, GitHub OAuth)
- Role-Based Access Control (RBAC): admin, user, readonly
- Rate limiting per user/role
- PBKDF2-SHA256 password hashing

### AI Capabilities
- Multi-model LLM support (Gemini → OpenRouter → DeepSeek fallback)
- Hybrid search (semantic + keyword)
- Semantic recall & memory consolidation
- Proactive suggestions & pattern detection
- Advanced reasoning with multi-step Chain-of-Thought
- Episodic, temporal, and graph memory

### Platform
- Team workspaces with shared memory
- Plugin marketplace (publish, search, rate)
- Webhook system for external integrations
- GraphQL API + REST API + WebSocket + SSE
- Admin dashboard with user management
- SOC2 compliance module
- Data residency region selection

### Billing & Usage
- Usage metering per event type
- Per-tool-call billing
- Stripe integration (subscriptions, payment intents)
- Quota management per plan (free/pro/enterprise)

---

## 🏗️ Architecture

```
aeryn-core-agent/
├── aeryn_core/              # Core business logic (147 modules)
│   ├── auth/                # Authentication, SSO, rate limiting
│   ├── billing/             # Billing, usage metering
│   ├── database/            # PostgreSQL (Neon) + SQLite + vector DB
│   ├── hermes/              # Hermes integration (brain, hands, reflex)
│   ├── memory/              # Vault, semantic, temporal, episodic memory
│   ├── platform/            # Webhooks, plugins, workspaces, integrations
│   ├── reasoning/           # Context, reasoning style, proactive engine
│   ├── safety/              # Security, guardrails, sandbox
│   └── utils/               # Logger, config, performance, adapters
├── apps/api/                # FastAPI daemon (:3010)
├── scripts/                 # Operational scripts (health, backup, deploy)
├── skills/                  # Procedural knowledge (dev, debug)
├── tests/                   # 597 tests
├── docs/                    # Documentation
├── sdk/                     # Python + TypeScript SDKs
└── Personalisasi/           # User data (Vault, Database, Persona)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| API Framework | FastAPI |
| Database | SQLite (local) + PostgreSQL/Neon (cloud) |
| Vector Search | pgvector + semantic indexing |
| Authentication | JWT + API Keys |
| AI/LLM | Gemini, OpenRouter, DeepSeek (fallback chain) |
| Real-time | WebSocket + SSE |
| Task Queue | asyncio background tasks |
| Deployment | PM2 |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python3 --version

# PM2 (process manager)
npm install -g pm2
```

### Installation

```bash
# Clone repository
git clone git@github.com:MuhammadApriansyah/Aeryn.git
cd Aeryn

# Create virtual environment
python3 -m venv venv-proot
source venv-proot/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Create .env file
cp .env.example .env

# Add your API keys
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

### Run

```bash
# Start with PM2
pm2 start ecosystem.config.js

# Or run directly
./venv-proot/bin/python apps/api/aeryn_api.py
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

See full API documentation for all 50+ endpoints.

---

## 🧪 Testing

```bash
# Run all tests
./venv-proot/bin/python -m pytest tests/ -v

# Run specific module tests
./venv-proot/bin/python -m pytest tests/test_auth/ -v

# With coverage
./venv-proot/bin/python -m pytest tests/ --cov=aeryn_core --cov-report=html
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
```

---

## 🔒 Security

- PBKDF2-SHA256 password hashing (100k iterations)
- JWT tokens with expiration
- SQL injection prevention (parameterized queries)
- Command injection prevention (no shell=True)
- Input sanitization & validation
- Rate limiting per endpoint
- CORS protection
- Audit logging

---

## 📊 Test Coverage

```
597 tests pass
0 failures
3 skipped (internal implementation tests)
```

---

## 📄 License

MIT License

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

---

*Built with ❤️ in Indonesia 🇮🇩*
