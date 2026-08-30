# Quick Start Guide

> **Purpose**: Ultra-fast setup in under 2 minutes.
> **Rule**: Real commands — copy-paste and go.

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/MuhammadApriansyah/Aeryn.git && cd Aeryn

# Setup
python3 -m venv venv-proot && source venv-proot/bin/activate && pip install -r requirements.txt

# Start
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# Verify
curl http://127.0.0.1:3010/health
```

Open `http://localhost:3010` — your dashboard is ready!

---

## 📋 First Commands Cheat Sheet

```bash
# Activate environment
source venv-proot/bin/activate

# Start server
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# Restart server
pm2 restart aeryn-api

# Check health
curl http://127.0.0.1:3010/health

# Run tests
python -m pytest tests/ -x -q

# Chat with Aeryn
curl -X POST http://127.0.0.1:3010/chat -H "Content-Type: application/json" -d '{"goal":"Hello","session_id":"default"}'

# Run a goal
curl -X POST http://127.0.0.1:3010/run -H "Content-Type: application/json" -d '{"goal":"Your goal","session_id":"default"}'

# Search
curl "http://127.0.0.1:3010/search?q=your+query&limit=10"
```

---

## 🆘 Need Help?

- **Docs**: `docs/onboarding/onboarding.md`
- **API Reference**: `docs/api/api-reference.md`
- **Development**: `CLAUDE.md` + `AGENTS.md`
- **Debugging**: `.claude/skills/aeryn-debugging.md`
