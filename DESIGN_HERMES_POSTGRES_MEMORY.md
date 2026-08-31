# Hermes PostgreSQL Memory Plugin — Design Document

## 1. Executive Summary

Plugin yang menjembatkan Hermes memory system (HOT/COLD tier) dengan PostgreSQL sebagai **unified persistent storage**. Tiap sesi selesai, ringkasan konteks otomatis disimpan ke PostgreSQL. Saat sesi baru dimulai, plugin auto-load memory yang relevan tanpa perlu MEMORY.md yang membengkak.

## 2. Problem Statement

### Masalah Saat Ini
- **MEMORY.md** dibatasi ~9K chars — tidak cukup untuk complex project context
- **Session search** lambat karena FTS5 di SQLite (tidak ada vector similarity)
- **Cold storage** di Android mount — unreliable, perlu sync manual
- **Cross-session context loss** — setelah compaction, detail granular hilang
- **No automatic memory lifecycle** — harus manual save ke memory library

### Kebutuhan
1. **Auto-save** session summary ke PostgreSQL tanpa user intervention
2. **Auto-load** relevant context saat session baru berdasarkan:
   - Current task similarity
   - Entity overlap (project, tools, files)
   - Temporal recency
   - User preference patterns
3. **Seamless integration** — tidak mengubah workflow existing
4. **Zero-config default** — jalan tanpa setup, opt-in advanced features

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Hermes Agent Core                         │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Session │  │  Tools   │  │  Memory    │  │  Skills  │  │
│  │ Manager │  │  Router  │  │  System    │  │  Loader  │  │
│  └────┬────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘  │
│       │             │              │               │        │
│       └─────────────┴──────────────┴───────────────┘        │
│                              │                              │
│                    ┌─────────▼──────────┐                   │
│                    │   Plugin Hooks     │                   │
│                    │   (Middleware)     │                   │
│                    └─────────┬──────────┘                   │
└──────────────────────────────┼──────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───────┐ ┌─────▼──────┐ ┌───────▼────────┐
     │  Auto-Save     │ │ Auto-Load  │ │  Maintenance   │
     │  Hook          │ │ Hook       │ │  Hook          │
     └────────┬───────┘ └─────┬──────┘ └───────┬────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  PostgreSQL Store   │
                    │  (Unified Storage)  │
                    └─────────────────────┘
```

## 4. Database Schema

### 4.1 Core Tables

```sql
-- Session summaries: compressed context per session
CREATE TABLE IF NOT EXISTS hermes.sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT UNIQUE NOT NULL,          -- Hermes session ID
    profile         TEXT NOT NULL DEFAULT 'default',
    title           TEXT,
    model           TEXT,
    provider        TEXT,
    source          TEXT,                          -- tui, whatsapp, discord, cron
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    message_count   INTEGER,
    tool_calls_count INTEGER,
    -- Compressed context (summary of what was done)
    summary         TEXT,                          -- LLM-generated summary
    summary_vector  vector(384),                   -- embedding for similarity
    -- Metadata
    project_dir     TEXT,                          -- working directory
    branches        TEXT[],                        -- git branches touched
    files_touched   TEXT[],                        -- file paths modified/read
    entities        JSONB,                         -- extracted entities
    tools_used      TEXT[],                        -- tools called in session
    divisions_used  TEXT[],                        -- divisions activated
    -- Lifecycle
    importance      FLOAT DEFAULT 0.5,             -- 0-1, computed score
    access_count    INTEGER DEFAULT 0,             -- how often referenced
    last_accessed   TIMESTAMPTZ,
    -- Tags & categories
    tags            TEXT[],
    category        TEXT,                          -- research, coding, ops, chat
    -- Raw transcript (compressed, for full recall)
    transcript_compressed BYTEA,                    -- gzip compressed JSON
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Memory entries: granular facts/learnings
CREATE TABLE IF NOT EXISTS hermes.memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT REFERENCES hermes.sessions(session_id),
    -- Content
    key             TEXT NOT NULL,                 -- lookup key
    value           TEXT NOT NULL,                 -- content
    value_vector    vector(384),                   -- for semantic search
    -- Classification
    tier            TEXT NOT NULL DEFAULT 'warm',  -- hot, warm, cold
    type            TEXT NOT NULL DEFAULT 'fact',  -- fact, lesson, preference, entity, task
    -- Source tracking
    source_type     TEXT,                          -- session, user_input, file_scan, cron
    source_detail   TEXT,                          -- which tool/skill generated this
    -- Entity extraction
    entities        JSONB,                         -- {projects: [], tools: [], files: []}
    -- Lifecycle
    confidence      FLOAT DEFAULT 1.0,             -- 0-1, how reliable
    importance      FLOAT DEFAULT 0.5,             -- 0-1, computed
    decay_rate      FLOAT DEFAULT 0.01,            -- per day
    last_reinforced TIMESTAMPTZ,                   -- when last confirmed
    access_count    INTEGER DEFAULT 0,
    last_accessed   TIMESTAMPTZ,
    -- TTL & cleanup
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMSTAMPTZ                     -- NULL = never expire
);

-- Projects: known projects with metadata
CREATE TABLE IF NOT EXISTS hermes.projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    dir_path        TEXT,
    tech_stack      TEXT[],
    dependencies    JSONB,                         -- {internal: [], external: []}
    session_count   INTEGER DEFAULT 0,
    last_active     TIMESTAMPTZ,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences & patterns
CREATE TABLE IF NOT EXISTS hermes.preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             TEXT UNIQUE NOT NULL,
    value           JSONB NOT NULL,
    confidence      FLOAT DEFAULT 1.0,
    evidence_count  INTEGER DEFAULT 1,             -- how many times observed
    last_observed   TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Entity registry: people, projects, tools, files
CREATE TABLE IF NOT EXISTS hermes.entities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,                 -- person, project, tool, file, concept
    aliases         TEXT[],
    metadata        JSONB,
    session_count   INTEGER DEFAULT 0,
    mention_count   INTEGER DEFAULT 0,
    last_mentioned  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, type)
);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS hermes.relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity   UUID REFERENCES hermes.entities(id),
    target_entity   UUID REFERENCES hermes.entities(id),
    relation_type   TEXT NOT NULL,                 -- uses, depends_on, created_by, part_of
    strength        FLOAT DEFAULT 1.0,
    evidence        TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_entity, target_entity, relation_type)
);
```

### 4.2 Indexes & Optimization

```sql
-- Vector similarity indexes (pgvector)
CREATE INDEX ON hermes.sessions USING ivfflat (summary_vector vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX ON hermes.memories USING ivfflat (value_vector vector_cosine_ops)
    WITH (lists = 100);

-- Performance indexes
CREATE INDEX ON hermes.sessions (session_id);
CREATE INDEX ON hermes.sessions (started_at DESC);
CREATE INDEX ON hermes.sessions (category);
CREATE INDEX ON hermes.sessions USING GIN (tags);
CREATE INDEX ON hermes.sessions USING GIN (tools_used);
CREATE INDEX ON hermes.sessions USING GIN (files_touched);

CREATE INDEX ON hermes.memories (key);
CREATE INDEX ON hermes.memories (tier);
CREATE INDEX ON hermes.memories (type);
CREATE INDEX ON hermes.memories (session_id);
CREATE INDEX ON hermes.memories (importance DESC);
CREATE INDEX ON hermes.memories USING GIN (entities);
CREATE INDEX ON hermes.memories (expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX ON hermes.entities (type, name);
CREATE INDEX ON hermes.entities USING GIN (aliases);

CREATE INDEX ON hermes.preferences (key);
```

### 4.3 Maintenance & Retention

```sql
-- View: active memories (not expired)
CREATE OR REPLACE VIEW hermes.active_memories AS
SELECT * FROM hermes.memories
WHERE expires_at IS NULL OR expires_at > NOW();

-- View: recent important sessions
CREATE OR REPLACE VIEW hermes.recent_sessions AS
SELECT * FROM hermes.sessions
WHERE started_at > NOW() - INTERVAL '30 days'
ORDER BY importance DESC, started_at DESC;

-- Materialized view: entity graph stats
CREATE MATERIALIZED VIEW hermes.entity_stats AS
SELECT
    e.name, e.type,
    e.mention_count, e.session_count,
    array_agg(DISTINCT r.relation_type) as relations,
    MAX(s.started_at) as last_session
FROM hermes.entities e
LEFT JOIN hermes.relationships r ON e.id IN (r.source_entity, r.target_entity)
LEFT JOIN hermes.sessions s ON s.session_id IN (
    SELECT session_id FROM hermes.memories m
    WHERE m.entities->>'projects' ? e.name
)
GROUP BY e.id;

-- Refresh materialized view concurrently
CREATE UNIQUE INDEX ON hermes.entity_stats (name, type);
```

## 5. Plugin Lifecycle

### 5.1 Auto-Save Flow

```
Session End Detection
        │
        ▼
┌───────────────────┐
│ 1. Trigger        │ ← Detect: session idle > N min, /exit, or explicit save
│    Detection      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 2. Context        │ ← Extract from session transcript
│    Extraction     │    - Messages, tool calls, files touched
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 3. LLM Summary    │ ← Generate compressed summary via LLM
│    Generation     │    - 1-3 paragraph summary
│                   │    - Key facts & decisions
│                   │    - Tools used, files modified
│                   │    - Lessons learned, errors encountered
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 4. Entity         │ ← Extract entities from session
│    Extraction     │    - Projects, files, tools, people
│                   │    - Update entity registry
│                   │    - Create relationships
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 5. Memory         │ ← Generate granular memories
│    Generation     │    - Facts: "Project X uses Fastify v4"
│                   │    - Lessons: "Always check sys.path before import"
│                   │    - Preferences: "User prefers concise Indonesian"
│                   │    - Tasks: "Dashboard V61.3 needs testing"
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 6. Embedding      │ ← Generate vector embeddings
│    Generation     │    - summary_vector (384d)
│                   │    - value_vector per memory
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 7. Persist to     │ ← Upsert to PostgreSQL
│    PostgreSQL     │    - sessions (1 row)
│                   │    - memories (N rows)
│                   │    - entities (upsert)
│                   │    - relationships (upsert)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 8. Update HOT     │ ← Update MEMORY.md with key facts
│    Memory         │    - Only if importance > threshold
└───────────────────┘
```

### 5.2 Auto-Load Flow

```
Session Start / New Context
        │
        ▼
┌───────────────────┐
│ 1. Context        │ ← Extract from current session
│    Analysis       │    - First user message
│                   │    - Working directory
│                   │    - Active project detection
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 2. Query          │ ← Build multi-signal query
│    Construction   │    - Text embedding of current task
│                   │    - Entity match (project, files)
│                   │    - Temporal decay (recent = higher)
│                   │    - User preference patterns
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 3. Multi-Signal   │ ← Query PostgreSQL
│    Retrieval      │    - Vector similarity (summary + memories)
│                   │    - Entity overlap scoring
│                   │    - Keyword match (FTS)
│                   │    - Recency + importance boost
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 4. Ranking &      │ ← Combine scores
│    Dedup          │    - Weighted: 0.4 vector + 0.3 entity + 0.2 recency + 0.1 keyword
│                   │    - Deduplicate similar memories
│                   │    - Filter expired/low-confidence
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 5. Context        │ ← Inject into session
│    Injection      │    - System prompt extension
│                   │    - Or: first user message prefix
│                   │    - Max 2K chars to avoid bloat
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 6. Update         │ ← Track what was loaded
│    Access Stats   │    - access_count++
│                   │    - last_accessed = NOW()
└───────────────────┘
```

## 6. Plugin API & Hooks

### 6.1 Hook Points

```python
# Plugin hooks into Hermes lifecycle

class PostgresMemoryPlugin:
    """Main plugin class"""

    # Lifecycle hooks
    async def on_session_start(self, session_info: dict) -> list[Memory]:
        """Called when new session starts. Returns memories to inject."""
        ...

    async def on_session_end(self, session_summary: dict) -> None:
        """Called when session ends. Saves to PostgreSQL."""
        ...

    async def on_tool_call(self, tool_name: str, args: dict, result: dict) -> None:
        """Called after each tool call. Extract facts/lessons."""
        ...

    async def on_file_change(self, file_path: str, action: str) -> None:
        """Called when file is created/modified/deleted."""
        ...

    async def on_user_message(self, message: str) -> list[Memory]:
        """Called on user input. Returns relevant memories."""
        ...

    async def on_compaction(self, messages: list[dict]) -> SessionSummary:
        """Called before context compression. Generate summary."""
        ...

    # Query API (for skills/agents)
    async def search(self, query: str, limit: int = 10,
                     filters: dict = None) -> list[Memory]:
        """Semantic search across all memories."""
        ...

    async def recall(self, key: str) -> Optional[Memory]:
        """Exact key lookup."""
        ...

    async def remember(self, key: str, value: str,
                       memory_type: str = "fact",
                       importance: float = 0.5,
                       ttl_days: int = None) -> Memory:
        """Store a new memory."""
        ...

    async def forget(self, key: str) -> bool:
        """Remove a memory."""
        ...

    async def get_entity(self, name: str, type: str = None) -> Optional[Entity]:
        """Get entity by name."""
        ...

    async def get_project_context(self, project_name: str) -> list[Memory]:
        """Get all memories related to a project."""
        ...

    async def get_stats(self) -> dict:
        """Get plugin statistics."""
        ...
```

### 6.2 Configuration

```yaml
# ~/.hermes/config.yaml
plugins:
  postgres_memory:
    enabled: true
    # Connection (required)
    connection:
      host: localhost
      port: 5432
      database: hermes
      user: hermes
      password: ${POSTGRES_PASSWORD}  # from .env
      ssl: false
      pool_size: 5

    # Auto-save settings
    auto_save:
      enabled: true
      trigger: idle          # idle, exit, explicit, compaction
      idle_minutes: 5        # save after N min of inactivity
      min_messages: 10       # don't save if < N messages
      generate_summary: true # use LLM to generate summary
      extract_entities: true
      extract_memories: true

    # Auto-load settings
    auto_load:
      enabled: true
      max_context_chars: 2000  # max chars to inject
      min_relevance: 0.3       # minimum score to include
      max_memories: 10         # max memories per query
      signals:
        vector_weight: 0.4
        entity_weight: 0.3
        recency_weight: 0.2
        keyword_weight: 0.1

    # Memory lifecycle
    lifecycle:
      hot_days: 7              # keep as HOT for N days
      warm_days: 30            # then downgrade to WARM
      cold_after: 90           # then COLD
      decay_enabled: true
      decay_rate: 0.01         # per day
      prune_after: 365         # delete after N days
      min_importance: 0.1      # prune if below

    # Embedding
    embedding:
      model: all-MiniLM-L6-v2  # 384d, fast, good quality
      device: cpu              # or cuda
      batch_size: 32

    # Security
    encryption:
      enabled: false           # encrypt at rest
      key_id:                  # KMS key

    # Performance
    cache:
      enabled: true
      ttl_seconds: 300         # cache query results
      max_entries: 1000

    # Logging
    log_level: INFO
```

### 6.3 CLI Commands

```bash
# Plugin management
hermes plugin enable postgres_memory
hermes plugin disable postgres_memory
hermes plugin status postgres_memory

# Memory operations
hermes memory search "aeryn dashboard"
hermes memory recall "aeryn_version"
hermes memory remember "key" "value" --type fact --importance 0.8
hermes memory forget "key"
hermes memory list --tier hot --limit 20
hermes memory stats

# Session operations
hermes session list --limit 10
hermes session show <session_id>
hermes session export <session_id> --format json
hermes session search "aeryn"

# Entity operations
hermes entity list --type project
hermes entity show <name>
hermes entity graph <name>  # show relationships

# Maintenance
hermes memory vacuum          # prune expired
hermes memory consolidate     # merge duplicates
hermes memory reindex         # rebuild embeddings
hermes memory backup --to s3  # backup to S3
```

## 7. Integration with Existing Memory System

### 7.1 HOT/WARM/COLD Tier Mapping

| Hermes Tier | PostgreSQL Tier | Criteria |
|-------------|-----------------|----------|
| MEMORY.md (HOT) | `tier = 'hot'` | Last 7 days, importance > 0.7 |
| Memory Library (COLD) | `tier = 'warm'` | 7-30 days, importance 0.3-0.7 |
| Archive | `tier = 'cold'` | 30-90 days, importance < 0.3 |
| Pruned | deleted | > 90 days OR importance < 0.1 |

### 7.2 MEMORY.md Sync

```python
async def sync_hot_memory(self):
    """Sync top-tier memories to MEMORY.md"""
    hot_memories = await self.db.query("""
        SELECT key, value FROM hermes.memories
        WHERE tier = 'hot' AND confidence > 0.7
        ORDER BY importance DESC, last_accessed DESC
        LIMIT 50
    """)

    # Generate compact MEMORY.md content
    content = "# HOT Memory (auto-synced from PostgreSQL)\n\n"
    for mem in hot_memories:
        content += f"- **{mem.key}**: {mem.value}\n"

    # Write to MEMORY.md (respecting 9K limit)
    write_file("MEMORY.md", content[:9000])
```

### 7.3 Session Search Integration

```python
async def session_search(self, query: str, limit: int = 5) -> list[Session]:
    """Enhanced session search with vector similarity"""
    # Generate query embedding
    query_vec = self.embed(query)

    # Multi-signal search
    results = await self.db.query("""
        SELECT s.*,
            1 - (s.summary_vector <=> $1) AS vec_sim,
            array_length(
                array_intersect(s.tags, $2), 1
            ) AS tag_overlap
        FROM hermes.sessions s
        WHERE s.started_at > NOW() - INTERVAL '90 days'
        ORDER BY (
            0.5 * (1 - (s.summary_vector <=> $1)) +
            0.3 * (array_length(array_intersect(s.tags, $2), 1)::float /
                    GREATEST(array_length($2, 1), 1)) +
            0.2 * EXP(-EXTRACT(EPOCH FROM NOW() - s.started_at) / 604800)
        ) DESC
        LIMIT $3
    """, query_vec, extract_tags(query), limit)

    return results
```

## 8. Security & Privacy

### 8.1 Data Protection

```python
class SecurityManager:
    """Handle encryption and access control"""

    # Encryption at rest (optional)
    async def encrypt(self, plaintext: str) -> bytes:
        """Encrypt sensitive memory values"""
        # Use AES-256-GCM with key from KMS
        ...

    async def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt memory values"""
        ...

    # Access control
    def check_access(self, memory: Memory, user: str) -> bool:
        """Check if user can access memory"""
        # Role-based access
        # Profile isolation
        ...

    # PII detection
    async def scan_pii(self, text: str) -> list[str]:
        """Detect PII in memory content"""
        # Use regex + NER model
        # Return list of PII types found
        ...

    # Secret redaction
    async def redact_secrets(self, text: str) -> str:
        """Redact API keys, tokens, passwords"""
        # Pattern matching for common secret formats
        ...
```

### 8.2 Credential Management

```yaml
# ~/.hermes/.env (never in config.yaml)
POSTGRES_PASSWORD=super_secret_password
POSTGRES_SSL_CERT=/path/to/cert.pem
```

```python
# Plugin loads credentials securely
import os
from hermes.utils.secrets import get_secret

password = get_secret("POSTGRES_PASSWORD")  # from .env or keyring
```

## 9. Performance Considerations

### 9.1 Latency Budget

| Operation | Target | Strategy |
|-----------|--------|----------|
| Auto-save trigger | < 100ms | Async, non-blocking |
| Memory search | < 200ms | pgvector index + cache |
| Session summary | < 5s | Background LLM call |
| Entity extraction | < 500ms | Rule-based + cache |
| Auto-load injection | < 300ms | Pre-computed on session start |

### 9.2 Resource Usage

| Resource | Budget | Notes |
|----------|--------|-------|
| PostgreSQL connections | 5-10 | Connection pool |
| Memory (plugin) | < 50MB | Embedding model + cache |
| Disk (embeddings) | ~10MB/1K memories | 384d float32 = 1.5KB each |
| Network | Minimal | Local PostgreSQL preferred |

### 9.3 Caching Strategy

```python
class Cache:
    """Multi-level cache"""

    # L1: In-memory (per session)
    l1_cache: dict = {}  # key -> Memory
    l1_ttl: int = 300    # 5 minutes

    # L2: Shared across sessions (Redis optional)
    l2_client = None  # Redis client if available

    # L3: PostgreSQL (source of truth)
    db: asyncpg.Pool
```

## 10. Migration & Backward Compatibility

### 10.1 From SQLite to PostgreSQL

```python
async def migrate_sqlite_to_postgres():
    """One-time migration from existing SQLite session DB"""

    # 1. Export all sessions from SQLite
    sqlite_sessions = sqlite_query("SELECT * FROM sessions")

    # 2. Transform and insert into PostgreSQL
    for session in sqlite_sessions:
        await postgres_execute("""
            INSERT INTO hermes.sessions (session_id, title, ...)
            VALUES ($1, $2, ...)
            ON CONFLICT (session_id) DO NOTHING
        """, ...)

    # 3. Migrate memory library
    memory_files = glob("~/.hermes/memory_library/**/*.md")
    for f in memory_files:
        content = read_file(f)
        await plugin.remember(
            key=stem(f),
            value=content,
            type="cold_storage"
        )
```

### 10.2 Backward Compatibility

- Plugin is **opt-in** — existing setups continue working
- If PostgreSQL unavailable, fallback to SQLite
- MEMORY.md remains primary HOT storage (plugin supplements, not replaces)
- All existing skills continue working unchanged

## 11. Monitoring & Observability

### 11.1 Metrics

```python
# Exposed via /plugin/postgres_memory/stats
{
    "total_sessions": 1523,
    "total_memories": 8472,
    "total_entities": 342,
    "hot_memories": 127,
    "warm_memories": 2341,
    "cold_memories": 6004,
    "avg_query_ms": 142,
    "cache_hit_rate": 0.73,
    "auto_save_count": 89,
    "auto_load_count": 156,
    "storage_mb": 245.7,
    "last_vacuum": "2026-08-31T03:00:00Z"
}
```

### 11.2 Health Check

```bash
hermes plugin health postgres_memory
# ✅ PostgreSQL connection: OK (12ms)
# ✅ pgvector extension: OK
# ✅ Embedding model: OK (all-MiniLM-L6-v2)
# ✅ Cache: OK (73% hit rate)
# ✅ Auto-save: OK (last save 2min ago)
# ✅ Auto-load: OK (last load 5min ago)
```

## 12. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Database schema creation
- [ ] Connection pool management
- [ ] Basic CRUD operations
- [ ] Configuration loading
- [ ] Health check endpoint

### Phase 2: Auto-Save (Week 2)
- [ ] Session end detection
- [ ] LLM summary generation
- [ ] Entity extraction
- [ ] Memory generation
- [ ] Embedding generation
- [ ] Persist to PostgreSQL

### Phase 3: Auto-Load (Week 3)
- [ ] Session start detection
- [ ] Multi-signal query construction
- [ ] Vector similarity search
- [ ] Ranking & deduplication
- [ ] Context injection
- [ ] Access stats tracking

### Phase 4: Lifecycle (Week 4)
- [ ] Tier management (hot/warm/cold)
- [ ] Decay & pruning
- [ ] MEMORY.md sync
- [ ] Migration from SQLite
- [ ] CLI commands

### Phase 5: Polish (Week 5)
- [ ] Caching layer
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation
- [ ] Integration tests

## 13. Open Questions for Sen

1. **Embedding model**: `all-MiniLM-L6-v2` (384d, fast) atau `text-embedding-3-small` (1536d, lebih akurat tapi perlu API key OpenAI)?

2. **Auto-save trigger**: `idle` (setelah N menit tidak aktif) atau `explicit` (hanya saat /save atau /exit)?

3. **Memory injection**: Langsung ke system prompt atau sebagai tool result di awal?

4. **Encryption**: Perlu encrypt at rest atau cukup password protection?

5. **Multi-profile**: Shared PostgreSQL atau isolated per profile?

6. **Conflict resolution**: Jika memori baru bertabrakan dengan existing, replace atau append?

7. **Backup strategy**: PostgreSQL dump harian atau continuous replication?

---

*Document version: 1.0*
*Created: 2026-08-31*
*Author: Hermes (Aeryn Core Team)*
