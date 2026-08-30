# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, expert automation features, enterprise workspace management, advanced workflow automation, production-grade observability, and **SPA Dashboard** frontend with full accessibility.

![Version](https://img.shields.io/badge/version-58.0-blue)
![Tests](https://img.shields.io/badge/tests-661%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-SPA-success)
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
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-success)
![Theme](https://img.shields.io/badge/theme-dark%2Flight-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Modern Frontend (V58)
- **SPA Dashboard**: Single Page Application with zero JavaScript dependencies
- **Full Accessibility**: WCAG 2.1 AA compliant — keyboard navigation, screen reader support, skip links
- **Real-time Health Check**: Dashboard polls backend every 5 seconds
- **Dark/Light Theme**: Toggle with localStorage persistence
- **Keyboard Shortcuts**: `Ctrl+K` search, `Ctrl+T` theme toggle, `Ctrl+/` help
- **Toast Notifications**: Success, error, info, warning feedback
- **Offline Detection**: Banner when backend API is unreachable
- **Loading Skeleton**: Shimmer animation during data fetch
- **Responsive Design**: Works on mobile and desktop
- **PM2 Integration**: Both frontend and backend managed by PM2

### Production-Grade Observability (V57)
- **Multi-Region Deploy**: Deploy to multiple AWS regions with Terraform
- **Distributed Tracing**: OpenTelemetry + Jaeger integration
- **Advanced Monitoring APM**: Prometheus metrics + Grafana dashboards

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

### Developer Experience (V50-V54)
- **Template Preview**: Visual thumbnails with features
- **Success Animation**: Celebration on completion
- **Debug Mode**: Verbose logging
- **Custom Templates**: Create and share templates
- **Diff Preview**: Before/after comparison
- **One-Click Generate**: Minimal questions, instant project
- **Post-Generate Guide**: Clear next steps
- **Progress Indicator**: Visual feedback during generation

### Fullstack AI Engineer (V46)
- **Fullstack CLI**: `new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`
- **Realistic Templates**: React + Fastify + SQLite
- **Migration System**: Database migrations with rollback
- **Generated Tests**: Tests that work out of the box

### Security & Safety (V42-V45)
- **4 Isolation Levels**: Basic, Namespace, Bubblewrap, Full
- **Prompt Injection Defense**: Multi-layer detection and blocking
- **Memory Guard**: Sensitive data encryption at rest
- **Zero Dependencies**: Works without Docker/Bubblewrap/root

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check (status, memory, version) |
| `GET /web/` | SPA Dashboard |
| `GET /api/py/health` | Health proxy |

---

## 📊 Test Coverage

```
661 tests pass
0 failures
```

---

## 📋 Quick Start

```bash
# Clone repo
git clone https://github.com/MuhammadApriysyah/Aeryn.git
cd Aeryn

# Setup backend
python3 -m venv venv-proot
source venv-proot/bin/activate
pip install -r requirements.txt

# Start backend + web UI
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# Access Dashboard
open http://localhost:3010/web/
```

---

## 📋 PM2 Commands

```bash
pm2 list              # List all processes
pm2 logs aeryn-api    # Backend logs
pm2 restart aeryn-api # Restart backend
pm2 save              # Save config
```

---

## 📁 Documentation

- [Changelog](CHANGELOG.md) — Version history
- [UI Recommendations](docs/ui-recommendations.md) — Development roadmap

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*

---

## 📄 License

MIT
