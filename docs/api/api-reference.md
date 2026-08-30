# API Reference (V59)

> **Purpose**: Complete API endpoint reference for Aeryn's backend.
> **Rule**: Real endpoints — all return actual data, no test doubles.

---

## 📋 Base URL

```
http://127.0.0.1:3010
```

Authentication: Bearer token in `Authorization` header for protected endpoints.

---

## 🩺 Health Check

### `GET /health`

Check system health.

**Response:**
```json
{
  "status": "healthy",
  "memory_mb": 24.3,
  "version": "40.44"
}
```

---

## 🏃 Run Goal

### `POST /run`

Execute a goal through the full cognitive pipeline.

**Request:**
```json
{
  "goal": "Analyze the codebase for security issues",
  "session_id": "default",
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "status": "ok",
  "session_id": "default",
  "goal": "Analyze the codebase for security issues",
  "steps": [...],
  "result": "...",
  "memory_id": "memory_12345",
  "execution_time_ms": 1250
}
```

---

## 💬 Chat

### `POST /chat`

Chat with Aeryn (conversational mode).

**Request:**
```json
{
  "goal": "Hello Aeryn, what can you do?",
  "session_id": "default"
}
```

**Response:**
```json
{
  "status": "ok",
  "response": "Hello! I'm Aeryn, your AI personal assistant...",
  "session_id": "default",
  "suggestions": ["What can you do?", "Help me write code"],
  "model": "nous:hermes-3-ib"
}
```

---

## 🔍 Search

### `GET /search`

Search Aeryn's knowledge base.

**Parameters:**
- `q` (required): Search query
- `limit` (optional, default: 10): Max results

**Response:**
```json
{
  "status": "ok",
  "query": "FastAPI best practices",
  "results": [...],
  "total": 42,
  "took_ms": 15
}
```

---

## 📝 Compile Prompt

### `POST /compile`

Compile user prompt into AI-ready context with memory + vault data.

**Request:**
```json
{
  "user_prompt": "How do I implement rate limiting?",
  "session_id": "default"
}
```

**Response:**
```json
{
  "status": "ok",
  "compiled_prompt": "...",
  "context_size": 12500,
  "vault_entries": 3,
  "memory_refs": 5
}
```

---

## 🧠 Digest Conversation

### `POST /digest`

Digest a conversation for memory storage.

**Request:**
```json
{
  "user_prompt": "Remember that I prefer dark mode",
  "response": "I've noted your preference for dark mode...",
  "session_id": "default"
}
```

**Response:**
```json
{
  "status": "ok",
  "memory_id": "memory_12346",
  "entities_extracted": ["dark mode"],
  "stored": true
}
```

---

## 📊 Dashboard Stats

### `GET /dashboard/stats`

Get dashboard statistics.

**Response:**
```json
{
  "status": "ok",
  "total_projects": 10,
  "total_workspaces": 3,
  "total_chat_sessions": 25,
  "total_plugins": 8,
  "total_audit_entries": 150
}
```

---

## 🔧 Adaptive System

### `GET /api/adaptive/health`

Get adaptive system health report.

**Response:**
```json
{
  "status": "healthy",
  "last_run": "2026-08-30T10:30:00",
  "error_count_24h": 5,
  "adaptation_count_24h": 2,
  "memory_usage_mb": 24.3
}
```

### `GET /api/adaptive/errors`

Get error summary.

**Response:**
```json
{
  "total_errors": 5,
  "breakdown": [
    {"pattern": "ConnectionError", "count": 3, "last_seen": "..."},
    {"pattern": "TimeoutError", "count": 2, "last_seen": "..."}
  ]
}
```

### `POST /api/adaptive/run-cycle`

Run a manual adaptive cycle.

**Response:**
```json
{
  "status": "ok",
  "cycle_id": "cycle_12345",
  "errors_detected": 2,
  "fixes_applied": 1,
  "adaptations": [...]
}
```

---

## 🧩 Plugin System

### `GET /plugins/list`

List available plugins.

**Response:**
```json
{
  "plugins": [
    {"name": "code-review", "enabled": true, "version": "1.0"},
    {"name": "research", "enabled": true, "version": "1.0"}
  ]
}
```

### `POST /plugins/install`

Install a plugin.

**Request:**
```json
{
  "name": "database-manager",
  "source": "local"
}
```

---

## 🔐 Auth & API Keys

### `POST /api/auth/login`

Get API token.

**Request:**
```json
{
  "api_key": "[REDACTED]"
}
```

**Response:**
```json
{
  "token": "[REDACTED]",
  "expires_in": 3600
}
```

### `GET /api/keys`

List user's API keys.

**Headers:** `Authorization: Bearer [token]`

---

## 💰 Billing

### `GET /billing/plans`

List subscription plans.

**Response:**
```json
{
  "plans": {
    "free": {"limit": 100, "price": 0},
    "pro": {"limit": "unlimited", "price": 9},
    "enterprise": {"limit": "unlimited", "price": 49}
  }
}
```

### `GET /billing/usage`

Get usage statistics.

**Headers:** `Authorization: Bearer [token]`

---

## 🤖 Multi-Agent

### `POST /api/agents/register`

Register a new agent.

**Request:**
```json
{
  "name": "my-agent",
  "role": "worker",
  "capabilities": ["python", "testing"]
}
```

### `GET /api/agents/list`

List all registered agents.

---

## 🌐 SPA Routes

These routes serve the dashboard HTML — client-side routing handles navigation:

| Route | Description |
|-------|-------------|
| `/` | Dashboard (default) |
| `/projects` | Projects page |
| `/workspaces` | Workspaces page |
| `/chat` | Chat page |
| `/settings` | Settings page |
| `/audit` | Audit trail page |

---

## ⚠️ Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 401 | Unauthorized |
| 429 | Rate limited |
| 500 | Internal error (auto-recovered by adaptive system) |

---

*API reference v59.0 — Updated 2026-08-30.*
