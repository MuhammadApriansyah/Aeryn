# Aeryn — PostgreSQL + pgvector Migration & Architecture

> Version: 1.0
> Date: 2026-08-28
> Status: APPROVED — Ready for execution
> Target: Personal Assistant Agent SaaS for Developer + Enterprise

---

## 1. Executive Summary

Aeryn saat ini menggunakan **30+ SQLite files** yang tersebar di 124 modules. Arsitektur ini tidak scalable untuk multi-user SaaS.

**Keputusan:** Migrasikan ke **PostgreSQL + pgvector** sebagai single source of truth.

**Prinsip:**
- Single-tenant → multi-tenant ready
- Zero budget → bootstrap friendly
- Bertahap → tidak mengganggu existing features

---

## 2. Current State Analysis

### 2.1 Database Files (30+ SQLite)

| Category | Count | Examples |
|---|---|---|
| Core Services | 10 | vault.db, shared.db, conversations.db, notifications.db |
| Memory System | 8 | graph_memory.db, enhanced_memory.db, semantic_search.db |
| Platform | 10 | auth.db, api_keys.db, usage.db, multi_tenant.db |
| Integrations | 5 | discord_bot.db, telegram_bot.db, github_integration.db |
| Unused Stubs | 6 | video_analysis.db, voice.db, speech_recognition.db |

### 2.2 Problems

| Problem | Impact | Severity |
|---|---|---|
| `database is locked` errors | Data loss, 500 errors | 🔴 Critical |
| No cross-module queries | Cannot join users + conversations + usage | 🔴 Critical |
| No connection pooling | Thrashing under load | 🟡 High |
| No migrations | Schema changes are manual | 🟡 High |
| 30+ files to backup | Operational nightmare | 🟡 Medium |
| No row-level security | Enterprise cannot use | 🟡 Medium |

---

## 3. Target Architecture

### 3.1 Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Aeryn API (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              PostgreSQL 16 + pgvector                │    │
│  │                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │    │
│  │  │  Relational   │  │  Vector      │  │  JSONB   │  │    │
│  │  │  Tables       │  │  Embeddings  │  │  Flex    │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLAlchemy   │  │  Alembic     │  │  PgBouncer   │      │
│  │  ORM          │  │  Migrations  │  │  Pool        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Why PostgreSQL + pgvector?

| Alternative | Why Not | Why PG + pgvector |
|---|---|---|
| SQLite (current) | No multi-user, file locking | ✅ Same SQL, production-grade |
| MySQL | No vector search native | ✅ pgvector extension |
| MongoDB | No ACID, no relational | ✅ Relational + JSONB |
| Qdrant only | No relational data | ✅ PG handles both |
| Qdrant + PG | Overkill for <100K vectors | ✅ pgvector sufficient |

---

## 4. Schema Design

### 4.1 Core Tables

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Organizations (for multi-tenant future)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'free', -- free, pro, team, enterprise
    billing_email TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user', -- admin, user, readonly
    status TEXT DEFAULT 'active', -- active, suspended, deleted
    settings JSONB DEFAULT '{}',
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    scopes JSONB DEFAULT '["read"]',
    last_used TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(org_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
```

### 4.2 Session & Conversation Tables

```sql
-- Chat Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    title TEXT DEFAULT 'New Session',
    metadata JSONB DEFAULT '{}',
    message_count INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages (with reasoning)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    reasoning JSONB DEFAULT '[]', -- 5-step CoT
    tokens INT DEFAULT 0,
    provider TEXT DEFAULT 'gemini',
    model TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_user ON messages(user_id);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_updated ON sessions(updated_at DESC);
```

### 4.3 Tasks & Notifications

```sql
-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    priority TEXT DEFAULT 'normal', -- low, normal, high, critical
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    title TEXT NOT NULL,
    body TEXT,
    priority TEXT DEFAULT 'normal',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
```

### 4.4 Vault & Memory (pgvector)

```sql
-- Vault (encrypted personal data)
CREATE TABLE vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    title TEXT NOT NULL,
    content TEXT, -- encrypted at application layer
    layer TEXT DEFAULT 'personal', -- personal, work, shared
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Memories (with vector embedding)
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    content TEXT NOT NULL,
    embedding vector(768), -- text-embedding-3-small or similar
    importance FLOAT DEFAULT 0.5,
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    source TEXT, -- conversation, vault, external
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Episodic Memory (timeline)
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- action, decision, milestone
    description TEXT NOT NULL,
    actors JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Semantic Index (documents, knowledge)
CREATE TABLE semantic_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_type TEXT, -- document, conversation, web
    source_id TEXT,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    indexed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector indexes (IVFFlat for performance)
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_semantic_embedding ON semantic_index USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_semantic_user ON semantic_index(user_id);
```

### 4.5 Usage & Billing

```sql
-- Usage Events (granular tracking)
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    event_type TEXT NOT NULL, -- request, token, storage, tool_call
    quantity FLOAT NOT NULL,
    unit TEXT NOT NULL, -- request, token, gb, call
    cost FLOAT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    plan TEXT NOT NULL, -- free, pro, team, enterprise
    status TEXT DEFAULT 'active', -- active, past_due, cancelled
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    stripe_subscription_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    subscription_id UUID REFERENCES subscriptions(id),
    amount FLOAT NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'draft', -- draft, open, paid, void
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    stripe_invoice_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_usage_user ON usage_events(user_id);
CREATE INDEX idx_usage_org ON usage_events(org_id);
CREATE INDEX idx_usage_created ON usage_events(created_at);
CREATE INDEX idx_subscriptions_org ON subscriptions(org_id);
```

### 4.6 Tools & Audit

```sql
-- Tool Executions
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    org_id UUID REFERENCES organizations(id),
    tool_name TEXT NOT NULL,
    params JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    duration_ms INT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Circuit Breakers
CREATE TABLE circuit_breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name TEXT UNIQUE NOT NULL,
    state TEXT DEFAULT 'closed', -- closed, open, half_open
    failure_count INT DEFAULT 0,
    last_failure TIMESTAMPTZ,
    last_success TIMESTAMPTZ,
    threshold INT DEFAULT 5,
    recovery_timeout INT DEFAULT 60,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Secrets (encrypted)
CREATE TABLE secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    value_encrypted TEXT NOT NULL,
    scope TEXT DEFAULT 'user', -- user, org
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    org_id UUID REFERENCES organizations(id),
    action TEXT NOT NULL, -- login, create, update, delete, api_call
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tool_exec_user ON tool_executions(user_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_org ON audit_log(org_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);
CREATE INDEX idx_secrets_user ON secrets(user_id);
```

---

## 5. Migration Strategy (Opsi B — Bertahap)

### Phase 0: Pre-Migration (Minggu 1)

```
Tujuan: Stabilize current SQLite setup

Tasks:
1. Fix response dedup bug
2. Add WAL mode + busy_timeout to all connections
3. Prune 6 unused modules
4. Add connection retry logic

Deliverable: Stable single-user app
Risk: Low
Rollback: N/A
```

### Phase 1: Auth System (Minggu 2)

```
Tujuan: Multi-user support

Tasks:
1. Create users, organizations, api_keys tables in SQLite
2. Implement JWT auth (access + refresh tokens)
3. Add RBAC middleware
4. Add API key authentication
5. Migrate existing data to user-scoped

Deliverable: Multi-user login
Risk: Low
Rollback: Keep auth optional, anonymous still works
```

### Phase 2: PostgreSQL Setup (Minggu 3)

```
Tugas: Dual-write architecture

Tasks:
1. Install PostgreSQL 16 locally
2. Install pgvector extension
3. Create all tables (Section 4)
4. Setup SQLAlchemy + Alembic
5. Implement dual-write layer (SQLite + PG)
6. Add health check for PG

Deliverable: Hybrid DB operational
Risk: Medium
Rollback: Read from SQLite if PG fails
```

### Phase 3: Data Migration (Minggu 4)

```
Tugas: Historical data → PostgreSQL

Tasks:
1. Export all 30 SQLite files to CSV/JSON
2. Transform to new schema
3. Import to PostgreSQL
4. Validate data consistency
5. Switch read path to PG
6. Keep SQLite as fallback (read-only)

Deliverable: PG as primary database
Risk: Medium
Rollback: Switch read path back to SQLite
```

### Phase 4: pgvector + Semantic Search (Minggu 5-6)

```
Tugas: Vector search capability

Tasks:
1. Setup embedding pipeline (OpenAI text-embedding-3-small)
2. Migrate semantic_search.db → memories table
3. Implement hybrid search (keyword + vector)
4. Add vector similarity threshold tuning
5. Benchmark: <100ms for 100K vectors

Deliverable: Production vector search
Risk: Low
Rollback: Keep semantic_search.db as fallback
```

### Phase 5: Cleanup (Minggu 7-8)

```
Tugas: Remove SQLite dependencies

Tasks:
1. Remove all SQLite connection code
2. Remove 30+ .db files
3. Update tests for PostgreSQL
4. Update documentation
5. Performance testing

Deliverable: PostgreSQL-only architecture
Risk: Low
Rollback: Git revert
```

---

## 6. Pricing Model

### 6.1 Usage-Based + Seat Option

```
┌──────────────────────────────────────────────────────────────────┐
│  Free        Pro           Team               Enterprise         │
│  $0/mo       $29/mo        $199/mo            Custom            │
├──────────────────────────────────────────────────────────────────┤
│  1K req/mo   10K req/mo    100K req/mo        Unlimited         │
│  1 seat      5 seats       25 seats           Custom            │
│  100 mem     10K mem       100K mem           Unlimited         │
│  Community   Email         Priority           Dedicated         │
│  Basic       MCP+API       SSO+Audit          SLA+SOC2          │
│                                                                   │
│  Overage: $0.001/request | $0.01/1K tokens | $0.05/1K memories  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Usage Tracking

```sql
-- Track every billable event
INSERT INTO usage_events (user_id, event_type, quantity, unit, cost)
VALUES (
    'user-uuid',
    'request',      -- request, token, storage, tool_call
    1,              -- quantity
    'request',      -- unit
    0.001           -- cost in USD
);

-- Monthly billing query
SELECT 
    user_id,
    event_type,
    SUM(quantity) as total_quantity,
    SUM(cost) as total_cost
FROM usage_events
WHERE created_at >= date_trunc('month', NOW())
GROUP BY user_id, event_type;
```

---

## 7. Security & Compliance

### 7.1 Row-Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Users can only see their own messages
CREATE POLICY messages_user_policy ON messages
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Org admins can see all org messages
CREATE POLICY messages_admin_policy ON messages
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = current_setting('app.current_user_id')::UUID
            AND role = 'admin'
        )
    );
```

### 7.2 Encryption at Rest

| Data | Method |
|---|---|
| Passwords | bcrypt (cost=12) |
| API Keys | SHA-256 hash |
| Vault content | AES-256-GCM (app layer) |
| Secrets | AES-256-GCM (app layer) |
| PII | Column-level encryption |

### 7.3 Audit Requirements

```sql
-- All data access logged
CREATE TABLE data_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    table_name TEXT,
    record_id UUID,
    action TEXT, -- SELECT, INSERT, UPDATE, DELETE
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-log via trigger
CREATE OR REPLACE FUNCTION log_access() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO data_access_log (user_id, table_name, record_id, action)
    VALUES (current_setting('app.current_user_id')::UUID, TG_TABLE_NAME, NEW.id, TG_OP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## 8. Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| API response (p50) | <50ms | histogram |
| API response (p95) | <200ms | histogram |
| API response (p99) | <500ms | histogram |
| Vector search (p95) | <100ms | histogram |
| Concurrent users | 1000+ | load test |
| Database connections | <100 | pg_stat_activity |
| Uptime | 99.9% | monitoring |

---

## 9. Backup & Recovery

### 9.1 Strategy

| Type | Frequency | Retention |
|---|---|---|
| Full backup | Daily | 30 days |
| WAL archiving | Continuous | 7 days |
| Point-in-time | Real-time | 7 days |

### 9.2 Commands

```bash
# Full backup
pg_dump -Fc aeryn > /backup/aeryn_$(date +%Y%m%d).dump

# Restore
pg_restore -d aeryn /backup/aeryn_20260828.dump

# Point-in-time recovery
# Use WAL archiving + recovery.conf
```

---

## 10. Monitoring

### 10.1 Key Metrics

```sql
-- Active users
SELECT COUNT(DISTINCT user_id) FROM sessions 
WHERE updated_at > NOW() - INTERVAL '24 hours';

-- Request volume
SELECT DATE_TRUNC('hour', created_at), COUNT(*) 
FROM usage_events 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1;

-- Error rate
SELECT 
    COUNT(*) FILTER (WHERE success = false) * 100.0 / COUNT(*) as error_rate
FROM tool_executions
WHERE created_at > NOW() - INTERVAL '1 hour';

-- Storage per org
SELECT 
    org_id,
    pg_size_pretty(pg_total_relation_size('messages')) as messages_size,
    pg_size_pretty(pg_total_relation_size('memories')) as memories_size;
```

### 10.2 Alerts

| Condition | Severity | Action |
|---|---|---|
| Error rate > 5% | 🔴 Critical | Page on-call |
| Response time > 500ms | 🟡 Warning | Investigate |
| DB connections > 80% | 🟡 Warning | Scale pool |
| Disk usage > 85% | 🔴 Critical | Add storage |
| Failed backups | 🔴 Critical | Fix immediately |

---

## 11. Cost Projection

### 11.1 Infrastructure (Self-Hosted)

| Item | Now | Month 3 | Month 6 | Month 12 |
|---|---|---|---|---|
| Server (existing) | $0 | $0 | $50/mo | $100/mo |
| PostgreSQL | SQLite (local) | Local PG | Local PG | Managed PG ($50) |
| Storage | 2GB | 10GB | 50GB | 200GB |
| Bandwidth | 100GB | 500GB | 2TB | 5TB |
| **Total/mo** | **$0** | **$0** | **$50** | **$150** |

### 11.2 Revenue Projection (Usage-Based)

| Month | Users | Paying | MRR | Notes |
|---|---|---|---|---|
| 1 | 10 | 0 | $0 | Friends & family |
| 2 | 50 | 5 | $145 | Early adopters |
| 3 | 150 | 15 | $435 | Product Hunt launch |
| 6 | 500 | 50 | $1,450 | Organic growth |
| 12 | 2000 | 200 | $5,800 | Enterprise deals |

---

## 12. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Data loss during migration | Low | 🔴 Critical | Full backup + dual-write |
| Performance regression | Medium | 🟡 High | Benchmark + rollback plan |
| pgvector not sufficient | Low | 🟡 Medium | Can add Qdrant later |
| Auth bypass | Low | 🔴 Critical | Security audit + pentest |
| Budget overrun | Low | 🟡 Medium | Self-hosted, scale gradually |
| Scope creep | High | 🟡 Medium | Strict roadmap adherence |

---

## 13. Open Decisions

| Decision | Options | Recommended |
|---|---|---|
| Embedding model | OpenAI vs local (all-MiniLM-L6-v2) | Local for cost, OpenAI for quality |
| ORM | SQLAlchemy vs raw SQL | SQLAlchemy + Alembic |
| Migration tool | Alembic vs custom | Alembic |
| Connection pool | PgBouncer vs SQLAlchemy pool | SQLAlchemy pool (simpler) |
| JSONB vs normalized | Hybrid | JSONB for flexible, normalized for query |

---

## 14. Approval

| Role | Name | Date | Signature |
|---|---|---|---|
| Author | Hermes (Aeryn System) | 2026-08-28 | ✅ |
| Reviewer | Sen | | |
| Approver | Sen | | |

---

## Appendix A: SQLite → PostgreSQL Mapping

| SQLite File | PostgreSQL Table | Notes |
|---|---|---|
| vault.db | vault | Add user_id, encrypt content |
| shared.db | tasks, notifications | Split into separate tables |
| conversations.db | sessions, messages | Restructure with FK |
| notifications.db | notifications | Merge with above |
| semantic_search.db | memories, semantic_index | Add pgvector |
| auth.db | users, organizations | Complete rewrite |
| api_keys.api_keys | api_keys | Similar structure |
| usage.db | usage_events | More granular |
| graph_memory.db | memories (type=graph) | Convert to vector |
| enhanced_memory.db | memories (type=enhanced) | Convert to vector |
| memory_decay.db | memories (with decay metadata) | JSONB metadata |
| memory_learning.db | memories (type=learning) | Convert to vector |
| episodic_memory.db | episodic_memories | New table |
| entity_resolution.db | JSONB in memories | Merge |
| proactive.db | briefings | Rename |
| briefings.db | briefings | Merge |
| patterns.db | JSONB in memories | Merge |
| secrets.db | secrets | Add encryption |
| multi_tenant.db | organizations | Rename |
| discord_bot.db | Remove | Not core |
| telegram_bot.db | Remove | Not core |
| github_integration.db | Remove | Not core |
| calendar_integration.db | Remove | Not core |
| email_agent.db | Remove | Not core |
| video_analysis.db | Remove | Unused |
| voice.db | Remove | Unused |
| speech_recognition.db | Remove | Unused |
| web_scraping.db | Remove | Unused |
| image_generation.db | Remove | Unused |
| finetuning.db | Remove | Unused |
| sandbox_audit.db | audit_log | Rename |
| cost_tracking.db | usage_events | Merge |
| sla_monitoring.db | usage_events | Merge |
| circuit_breakers.db | circuit_breakers | Similar |
| long_horizon.db | sessions (type=long) | JSONB metadata |
| supersession.db | Remove | Not needed |
| websocket.db | Remove | Stateless |
| mcp_auth.db | api_keys | Merge |
| cloud_sync.db | Remove | Not core |
| hermes_reflex.db | Remove | Not core |

**Result:** 30+ SQLite files → 20 PostgreSQL tables

---

*End of document.*
