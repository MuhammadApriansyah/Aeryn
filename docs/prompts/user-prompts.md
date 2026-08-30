# User Prompt Templates

> **Purpose**: Standardized user prompts for common Aeryn interactions.
> **Rule**: These are real prompts that produce real results — copy-paste ready.

---

## 💻 Developer Prompts

### Run a Goal

```
Run this goal: [YOUR_GOAL_HERE]
Session ID: [SESSION_NAME]
```

Example:
```
Run this goal: Analyze the codebase at /home/user/project for security vulnerabilities. Check for XSS, SQL injection, and unvalidated inputs. Generate a detailed report.
Session ID: security-audit-001
```

### Chat with Aeryn

```
Chat with Aeryn: [YOUR_MESSAGE_HERE]
Session ID: [SESSION_NAME]
```

Example:
```
Chat with Aeryn: Help me write a FastAPI endpoint with SQLite database integration. Include error handling and rate limiting.
Session ID: dev-help-001
```

### Search Knowledge

```
Search Aeryn's knowledge base: [QUERY]
Limit: 10
```

Example:
```
Search Aeryn's knowledge base: Python FastAPI best practices for async database connections
Limit: 15
```

---

## 📊 Analytics Prompts

### Generate Daily Briefing

```
Generate my daily briefing. Include:
1. System health status
2. Top 3 priorities for today
3. Any pending tasks or reminders
4. Recent knowledge additions
Session ID: daily-briefing
```

### System Audit

```
Perform a full system audit:
1. Check all API endpoints
2. Verify memory integrity
3. Scan for security issues
4. Report any errors or anomalies
Session ID: audit-001
```

---

## 🛠️ Operations Prompts

### Emergency Restart

```
Emergency: My Aeryn server is unresponsive. Restart it, check health, and report status.
```

### Clear Cache

```
Clear all caches and temporary files. Restart the backend and verify health.
```

### Backup Data

```
Backup all data to a timestamped archive. Include:
1. SQLite databases
2. Vault content
3. Configuration files
```

---

## 🎯 Workflow Prompts

### Code Review

```
Review this code for security, performance, and best practices:

[CODE_HERE]

Provide severity ratings: critical / warning / info
```

### Research Deep Dive

```
Research deep dive: [TOPIC]
Include:
1. Current state of the art
2. Key papers/references
3. Implementation considerations
4. Trade-offs to consider
```

### Planning & Strategy

```
Create a detailed implementation plan for: [GOAL]

Include:
1. Prerequisites
2. Step-by-step tasks
3. Risk assessment
4. Timeline estimate
5. Success criteria
```

---

## ⚡ Quick Commands

### One-liners (copy-paste ready):

```bash
# Health check
curl http://127.0.0.1:3010/health

# Restart backend
pm2 restart aeryn-api

# Run tests
python -m pytest tests/ -x -q

# Start new session
python -c "from aeryn_core.memory.vault import AerynVault; v=AerynVault(); v.store_entry(layer='wiki', title='Test', content='Hello')"

# Search vault
curl "http://127.0.0.1:3010/search?q=query&limit=10"

# Run a goal
curl -X POST http://127.0.0.1:3010/run -H "Content-Type: application/json" -d '{"goal":"Your goal here","session_id":"default"}'

# Chat with Aeryn
curl -X POST http://127.0.0.1:3010/chat -H "Content-Type: application/json" -d '{"goal":"Hello Aeryn","session_id":"default"}'
```
