# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, and **native sandbox with conditional security**.

![Version](https://img.shields.io/badge/version-45.0-blue)
![Tests](https://img.shields.io/badge/tests-619%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![MCP](https://img.shields.io/badge/mcp-protocol-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Native Sandbox (NEW in V45)
- **Conditional Security**: Auto-detect environment → use best available isolation level
- **Directed Fallback**: Graceful degradation if higher levels fail
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full
- **Resource Limits**: Memory, CPU, file descriptors via `resource.setrlimit()`
- **Command Whitelist**: Only approved commands can execute
- **Filesystem Isolation**: Temp directory per execution
- **Zero Dependencies**: Works without Docker, Bubblewrap, or root

### MCP Protocol (V43)
- **MCP Server**: Serve tools, resources, prompts to external MCP clients
- **MCP Client**: Connect to external MCP servers and invoke tools
- **MCP Registry**: Manage multiple MCP server connections

### Multi-Agent Orchestration (V43)
- **Workflow Engine**: Coordinate multiple agents for complex tasks
- **Task Management**: Priority-based task execution with dependencies
- **Agent Registry**: Register agents with capabilities

### Integration SDK (V43)
- **Developer SDK**: Build third-party integrations
- **Integration Registry**: Manage integrations and versions

### Security-First Architecture (V42)
- **Prompt Injection Defense**: Input sanitization, output validation
- **Memory Injection Defense**: Integrity verification, access audit
- **Tool Permission Limits**: Risk-based tool access, blast radius reduction
- **Model Routing**: Tiered model selection (60-70% cost reduction)
- **Token Monitoring**: Per-request tracking, budget enforcement

### Adaptive Rule Engine (V42)
- **Hot-reloadable rules** — Change behavior without restart
- **Priority-based evaluation** — Higher priority rules execute first

---

## 🏗️ Architecture

```
Aeryn/
├── aeryn_core/              ← Python (170+ modules)
│   ├── auth/                ← Auth, SSO, rate limiting
│   ├── billing/             ← Billing, usage metering
│   ├── cost/                ← Token monitoring, model routing
│   ├── database/            ← VectorDB, SQLite, Neon PG
│   ├── hermes_bridge/       ← Hermes adapter (shared skills/scripts)
│   ├── infra/               ← Agent templates + CLI
│   ├── integrations/        ← Integration SDK
│   ├── mcp/                 ← MCP server + client
│   ├── memory/              ← Vault, semantic, temporal
│   ├── multi_agent/         ← Multi-Agent orchestrator
│   ├── personal/            ← Proactive engine + personalization
│   ├── platform/            ← Webhooks, plugins, workspaces
│   ├── reasoning/           ← Context, reasoning style
│   ├── safety/              ← Security, guardrails
│   ├── sandbox/             ← NEW: Native sandbox (4 levels)
│   └── security/            ← Prompt injection, memory guard, tool permissions, dashboard
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 619 tests
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

## 📚 Native Sandbox

### 4 Isolation Levels

| Level | Name | Requirements | Isolation |
|-------|------|--------------|-----------|
| 0 | Basic | None | Resource limits + whitelist + tempdir |
| 1 | Namespace | `unshare` syscall | PID/UTS/IPC isolation + resource limits |
| 2 | Bubblewrap | `apt install bubblewrap` | Filesystem + full namespace isolation |
| 3 | Full | Bubblewrap + secimport + root | Maximum isolation with eBPF |

### Usage

```python
from aeryn_core.sandbox import fallback_orchestrator

# Auto-detect best available level
result = fallback_orchestrator.execute(["python3", "script.py"])
print(result["sandbox"])  # "basic", "namespace", "bubblewrap", or "full"
print(result["stdout"])

# Check current capabilities
status = fallback_orchestrator.status()
print(f"Level: {status['level']}")
print(f"Capabilities: {status['capabilities']}")
```

### Fallback Behavior

```
Level 3 (Full) → fails → Level 2 (Bubblewrap) → fails → Level 1 (Namespace) → fails → Level 0 (Basic)
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
619 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
