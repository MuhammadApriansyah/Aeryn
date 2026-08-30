# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with real-time dashboard, accessibility-first design, and multi-model LLM support.

![Version](https://img.shields.io/badge/version-58.0-blue)
![Tests](https://img.shields.io/badge/tests-661%20passed-brightgreen)
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-success)
![Theme](https://img.shields.io/badge/theme-dark%2Flight-success)
![Keyboard](https://img.shields.io/badge/keyboard-shortcuts-success)

---

## 🚀 Quick Start

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

# Access
open http://localhost:3010/web/
```

---

## 🎨 Features

### Dashboard (V58)
- **SPA Interface**: 7 pages — Dashboard, Projects, Workspaces, Chat, Plugins, Audit, Settings
- **Real-time Health**: Auto-refresh every 5 seconds
- **Toast Notifications**: Success, error, info, warning
- **Offline Banner**: Detects backend API status
- **Loading Skeleton**: Shimmer animation
- **Breadcrumb Navigation**: Shows page hierarchy
- **Skip Link**: Skip to main content for keyboard users
- **Keyboard Shortcuts**: `Ctrl+K` search, `Ctrl+T` theme, `Ctrl+/` help
- **Theme Toggle**: Dark/Light mode
- **Responsive Design**: Mobile-friendly
- **Accessibility**: ARIA labels, reduced motion, high contrast

### Health Check
- **Backend Status**: online/offline
- **Memory Usage**: Real-time MB
- **Version**: Current version
- **Uptime**: Live counter

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /web/` | Dashboard SPA |
| `GET /api/py/health` | Health proxy |

---

## 📊 Test Coverage

```
661 tests pass
0 failures
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

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
