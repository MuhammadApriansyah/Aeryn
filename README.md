# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, expert automation features, enterprise workspace management, advanced workflow automation, and **production-grade observability**.

![Version](https://img.shields.io/badge/version-57.0-blue)
![Tests](https://img.shields.io/badge/tests-661%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-web-success)
![Templates](https://img.shields.io/badge/templates-custom-success)
![Debug](https://img.shields.io/badge/debug-mode-success)
![Headless](https://img.shields.io/badge/headless-mode-success)
![Batch](https://img.shields.io/badge/batch-generate-success)
![Workspace](https://img.shields.io/badge/workspace-multi--tenant-success)
![Audit](https://img.shields.io/badge/audit-trail-success)
![Cache](https://img.shields.io/badge/cache-redis-success)
![Queue](https://img.shields.io/badge/job-queue-success)
![Workflow](https://img.shields.io/badge/workflow-dsl-success)
![MultiRegion](https://img.shields.io/badge/multi--region-deploy-success)
![Tracing](https://img.shields.io/badge/distributed--tracing-success)
![APM](https://img.shields.io/badge/apm-monitoring-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Production-Grade Observability (NEW in V57)
- **Multi-Region Deploy**: Deploy to multiple AWS regions with load balancing
- **Distributed Tracing**: OpenTelemetry integration for production debugging
- **Advanced Monitoring APM**: Prometheus metrics and Grafana dashboards

### Advanced Workflow Automation (V56)
- **Workflow DSL**: Define custom generation workflows with YAML/JSON
- **Headless Mode**: `--non-interactive` for fully automated CI/CD
- **Config File**: `.aerynrc` for project defaults with dot notation
- **Batch Generate**: Generate multiple projects from JSON config
- **Template Inheritance**: Extend templates from other templates
- **Custom Generators**: Replace default generators with custom logic

### Enterprise Features (V55)
- **Workspace Management**: Multi-tenant workspaces with RBAC
- **Audit Trail**: Track all actions for compliance
- **Rate Limiting**: Built-in API rate limiter
- **Cache Layer**: Redis caching template
- **Job Queue**: Background job processing (Bull)

### Beginner-Friendly UI (V47-V50)
- **Setup Wizard**: `aeryn start`
- **Visual Dashboard**: Web UI at port 3020
- **One-Click Generate**: Minimal questions
- **Error Solver**: Friendly error messages

### Fullstack AI Engineer (V46)
- **Fullstack CLI**: `new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`
- **Realistic Templates**: React + Fastify + SQLite
- **Migration System**: Database migrations with rollback

### Native Sandbox (V45)
- **Conditional Security**: Auto-detect → best isolation level
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full

### MCP Protocol (V43)
- **MCP Server/Client**: Standard compliance

### Security-First (V42)
- **Prompt Injection Defense**: Input sanitization, output validation
- **Memory Injection Defense**: Integrity verification
- **Tool Permission Limits**: Risk-based access
- **Model Routing**: Tiered selection (60-70% cost reduction)

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
# Option 1: Setup Wizard
aeryn start

# Option 2: One-Click Generate
aeryn new my-app --template react

# Option 3: Visual Dashboard
aeryn dashboard

# Option 4: Headless Mode
aeryn new my-app --non-interactive --template react

# Option 5: Batch Generate
aeryn batch projects.json

# Option 6: Workflow DSL
aeryn run workflow.yaml

# Option 7: Multi-Region Deploy
aeryn deploy --multi-region us-east,eu-west,ap-southeast
```

---

## 📚 Commands

| Command | Description |
|---------|-------------|
| `aeryn start` | Interactive setup wizard |
| `aeryn dashboard` | Launch visual dashboard |
| `aeryn new <name> [--template] [--non-interactive]` | Create new project |
| `aeryn batch <config.json>` | Batch generate projects |
| `aeryn run <workflow.yaml>` | Run custom workflow |
| `aeryn dev [--port 3010]` | Start development server |
| `aeryn db:migrate` | Run migrations |
| `aeryn db:seed` | Seed database |
| `aeryn test [--watch] [--coverage]` | Run tests |
| `aeryn build [--target node\|static]` | Build production |
| `aeryn deploy [--target pm2\|docker\|vercel\|multi-region]` | Deploy |
| `aeryn debug` | Enable debug mode |
| `aeryn templates` | List available templates |
| `aeryn plugins` | List installed plugins |
| `aeryn config` | Show current config |
| `aeryn workspace list` | List workspaces |
| `aeryn audit` | View audit trail |

---

## 📋 .aerynrc Config File

```json
{
  "version": "1.0",
  "defaults": {
    "template": "react",
    "database": "sqlite",
    "auth": true,
    "testing": true,
    "ci_cd": true,
    "rate_limiting": true,
    "caching": true,
    "job_queue": false,
    "tracing": true,
    "monitoring": true
  },
  "plugins": ["auth"],
  "environments": {
    "development": {"port": 3010},
    "staging": {"port": 3011},
    "production": {"port": 3012}
  },
  "regions": ["us-east", "eu-west"]
}
```

---

## 🔧 Workflow DSL Example

```yaml
name: "Full-Stack Deploy"
on_error: stop
steps:
  - name: generate
    action: generate
    params: {name: my-app, template: react}
  - name: test
    action: run_tests
  - name: deploy
    action: deploy
    params: {target: pm2}
```

---

## 🌍 Multi-Region Deploy

```bash
# Deploy to multiple AWS regions
aeryn deploy --multi-region us-east,eu-west,ap-southeast

# Generated structure:
# - Terraform configs for each region
# - Application Load Balancer
# - Auto-scaling groups
# - Health checks per region
```

---

## 🔍 Distributed Tracing (OpenTelemetry)

```bash
# Auto-generated tracing config
aeryn new my-app --template react

# Generated files:
# - config/tracing.js (OpenTelemetry + Jaeger)
# - Automatic span creation per request
# - Trace propagation across services
```

---

## 📊 Advanced Monitoring (Prometheus APM)

```bash
# Auto-generated monitoring config
aeryn new my-app --template react

# Generated files:
# - config/monitoring.js (Prometheus metrics)
# - /metrics endpoint for scraping
# - Grafana dashboard JSON
# - Alert rules
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
661 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
