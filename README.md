# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, and integration SDK.

![Version](https://img.shields.io/badge/version-43.0-blue)
![Tests](https://img.shields.io/badge/tests-606%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![MCP](https://img.shields.io/badge/mcp-protocol-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### MCP Protocol (NEW in V43)
- **MCP Server**: Serve tools, resources, prompts to external MCP clients
- **MCP Client**: Connect to external MCP servers and invoke tools
- **MCP Registry**: Manage multiple MCP server connections
- **Tool Discovery**: Automatic tool/resource/prompt discovery

### Multi-Agent Orchestration (NEW in V43)
- **Workflow Engine**: Coordinate multiple agents for complex tasks
- **Task Management**: Priority-based task execution with dependencies
- **Agent Registry**: Register agents with capabilities
- **Workflow Status**: Real-time workflow monitoring

### Integration SDK (NEW in V43)
- **Developer SDK**: Build third-party integrations
- **Integration Registry**: Manage integrations
- **Categories**: Organize by CRM, Communication, Development, etc.
- **Version Control**: Track integration versions

### Security-First Architecture (V42)
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
├── aeryn_core/              ← Python (155+ modules)
│   ├── auth/                ← Auth, SSO, rate limiting
│   ├── billing/             ← Billing, usage metering
│   ├── cost/                ← Token monitoring, model routing
│   ├── database/            ← VectorDB, SQLite, Neon PG
│   ├── hermes_bridge/       ← Hermes adapter (shared skills/scripts)
│   ├── integrations/        ← NEW: Integration SDK
│   ├── mcp/                 ← NEW: MCP server + client
│   ├── memory/              ← Vault, semantic, temporal
│   ├── multi_agent/         ← NEW: Multi-Agent orchestrator
│   ├── platform/            ← Webhooks, plugins, workspaces
│   ├── reasoning/           ← Context, reasoning style
│   ├── safety/              ← Security, guardrails
│   └── security/            ← Prompt injection, memory guard, tool permissions
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 606 tests
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

## 📚 MCP Protocol

### Registering a Tool (Server)
```python
from aeryn_core.mcp import mcp_server

mcp_server.register_tool(
    name="search",
    description="Search the web",
    input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    handler="search_handler"
)
```

### Calling an External Tool (Client)
```python
from aeryn_core.mcp import mcp_registry

client = mcp_registry.register("github", "http://mcp-github.com")
result = client.call_tool("search_repos", {"query": "aeryn"})
```

---

## 🤖 Multi-Agent Orchestration

```python
from aeryn_core.multi_agent import orchestrator, Task

# Register agents
orch.register_agent("researcher", "Researcher", ["search", "analyze"])
orch.register_agent("writer", "Writer", ["write", "edit"])

# Create workflow
workflow = orch.create_workflow("Research & Write", "Research and write article")

# Add tasks
task1 = Task("Research", "Research topic", "researcher", {"topic": "AI safety"})
task2 = Task("Write", "Write article", "writer", {}, dependencies=[task1.id])

workflow.add_task(task1)
workflow.add_task(task2)

# Execute
result = orch.execute_workflow(workflow.id)
```

---

## 🔧 Integration SDK

```python
from aeryn_core.integrations import integration_sdk

# Register integration
integration_sdk.register(
    name="slack",
    description="Slack integration",
    author="Aeryn",
    version="1.0.0",
    category="communication",
    config_schema={"type": "object"},
    endpoint="http://localhost/slack"
)

# Call integration
result = integration_sdk.call("slack", "send_message", {"text": "Hello!"})
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

### Memory Injection Defense
- Memory integrity verification
- Session isolation enforcement
- Memory access audit logging

### Tool Permission System
- Risk classification (LOW, MEDIUM, HIGH, CRITICAL)
- Confirmation required for high-stakes actions
- Session-based tool access limits

### Cost Optimization
- Token usage tracking per request
- Cost attribution by team/feature/user
- Model routing (tiered selection)
- Budget enforcement

---

## 📊 Test Coverage

```
606 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
