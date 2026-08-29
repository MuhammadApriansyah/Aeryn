# Aeryn — PostgreSQL Migration Workflow

> Version: 1.0
> Date: 2026-08-28
> Status: READY FOR REVIEW
> Approved: Pending Sen's signature

---

## 📌 GOALS

| # | Goal | Success Metric |
|---|---|---|
| G1 | Migrate from 30+ SQLite to PostgreSQL | 1 .db file → 20 tables |
| G2 | Add multi-user auth | JWT + RBAC working |
| G3 | Add pgvector semantic search | <100ms recall |
| G4 | Zero downtime migration | No data loss |
| G5 | Usage-based billing ready | Stripe integration |

---

## 📋 TASKS & TODOS

### Phase 0: Stabilize (Minggu 1)

#### Task 0.1: Fix Response Dedup Bug

| # | Todo | Status | Time |
|---|---|---|---|
| 0.1.1 | Identify all double-write paths | ⬜ | 30 min |
| 0.1.2 | Remove `router.memory.store()` calls (keep `session.add_message` only) | ⬜ | 1 jam |
| 0.1.3 | Verify single source of truth in monitoring | ⬜ | 30 min |
| 0.1.4 | Test: send message, verify 1 entry in history | ⬜ | 30 min |

**Definition of Done:** Setiap response muncul 1x di history, bukan 2x.

---

#### Task 0.2: Fix SQLite Locking

| # | Todo | Status | Time |
|---|---|---|---|
| 0.2.1 | Add `PRAGMA journal_mode=WAL` to all connections | ⬜ | 1 jam |
| 0.2.2 | Add `PRAGMA busy_timeout=5000` to all connections | ⬜ | 1 jam |
| 0.2.3 | Add retry logic (3 attempts, exponential backoff) | ⬜ | 2 jam |
| 0.2.4 | Test: 10 concurrent requests, zero "database is locked" | ⬜ | 1 jam |

**Definition of Done:** `database is locked` error = 0.

---

#### Task 0.3: Prune Unused Modules

| # | Todo | Status | Time |
|---|---|---|---|
| 0.3.1 | Delete `video_analysis.py` + `video_analysis.db` | ⬜ | 15 min |
| 0.3.2 | Delete `voice_interface.py` + `voice.db` | ⬜ | 15 min |
| 0.3.3 | Delete `speech_recognition.py` + `speech_recognition.db` | ⬜ | 15 min |
| 0.3.4 | Delete `web_scraping.py` + `web_scraping.db` | ⬜ | 15 min |
| 0.3.5 | Delete `image_generation.py` + `image_generation.db` | ⬜ | 15 min |
| 0.3.6 | Delete `finetuning.py` + `finetuning.db` | ⬜ | 15 min |
| 0.3.7 | Remove related endpoints from `aeryn_api.py` | ⬜ | 1 jam |
| 0.3.8 | Run tests, verify no regressions | ⬜ | 1 jam |

**Definition of Done:** 6 modules removed, tests pass.

---

### Phase 1: Auth System (Minggu 2)

#### Task 1.1: Database Schema (SQLite)

| # | Todo | Status | Time |
|---|---|---|---|
| 1.1.1 | Create `organizations` table | ⬜ | 30 min |
| 1.1.2 | Create `users` table | ⬜ | 30 min |
| 1.1.3 | Create `api_keys` table | ⬜ | 30 min |
| 1.1.4 | Add indexes (email, key_hash, user_id) | ⬜ | 30 min |
| 1.1.5 | Create migration script | ⬜ | 1 jam |

**Definition of Done:** 3 tables created with proper constraints.

---

#### Task 1.2: JWT Authentication

| # | Todo | Status | Time |
|---|---|---|---|
| 1.2.1 | Install `python-jose` + `passlib[bcrypt]` | ⬜ | 15 min |
| 1.2.2 | Implement `create_access_token()` | ⬜ | 1 jam |
| 1.2.3 | Implement `create_refresh_token()` | ⬜ | 30 min |
| 1.2.4 | Implement `verify_token()` | ⬜ | 30 min |
| 1.2.5 | Implement `get_current_user()` dependency | ⬜ | 1 jam |
| 1.2.6 | Add `/auth/register` endpoint | ⬜ | 1 jam |
| 1.2.7 | Add `/auth/login` endpoint | ⬜ | 1 jam |
| 1.2.8 | Add `/auth/refresh` endpoint | ⬜ | 30 min |
| 1.2.9 | Add `/auth/me` endpoint | ⬜ | 30 min |

**Definition of Done:** User bisa register, login, akses protected endpoint.

---

#### Task 1.3: API Key Authentication

| # | Todo | Status | Time |
|---|---|---|---|
| 1.3.1 | Implement `generate_api_key()` | ⬜ | 30 min |
| 1.3.2 | Implement `hash_api_key()` | ⬜ | 15 min |
| 1.3.3 | Implement `verify_api_key()` | ⬜ | 30 min |
| 1.3.4 | Add `/auth/api-keys` CRUD endpoints | ⬜ | 1 jam |
| 1.3.5 | Add API key middleware | ⬜ | 1 jam |
| 1.3.6 | Test: access endpoint with API key | ⬜ | 30 min |

**Definition of Done:** API key bisa dibuat, di-revoke, dan digunakan untuk auth.

---

#### Task 1.4: Role-Based Access Control (RBAC)

| # | Todo | Status | Time |
|---|---|---|---|
| 1.4.1 | Define roles: admin, user, readonly | ⬜ | 15 min |
| 1.4.2 | Implement `require_role()` decorator | ⬜ | 30 min |
| 1.4.3 | Apply RBAC to all existing endpoints | ⬜ | 2 jam |
| 1.4.4 | Add admin-only endpoints (user management) | ⬜ | 1 jam |
| 1.4.5 | Test: readonly user cannot write | ⬜ | 30 min |

**Definition of Done:** RBAC enforced di semua endpoints.

---

### Phase 2: PostgreSQL Setup (Minggu 3)

#### Task 2.1: Install & Configure PostgreSQL

| # | Todo | Status | Time |
|---|---|---|---|
| 2.1.1 | Install PostgreSQL 16 | ⬜ | 30 min |
| 2.1.2 | Install pgvector extension | ⬜ | 15 min |
| 2.1.3 | Create `aeryn` database | ⬜ | 15 min |
| 2.1.4 | Create `aeryn` user with password | ⬜ | 15 min |
| 2.1.5 | Configure `postgresql.conf` (shared_buffers, work_mem) | ⬜ | 30 min |
| 2.1.6 | Configure `pg_hba.conf` (local auth) | ⬜ | 15 min |
| 2.1.7 | Test connection from Python | ⬜ | 15 min |

**Definition of Done:** `psql -d aeryn` connects, `CREATE EXTENSION vector` works.

---

#### Task 2.2: SQLAlchemy + Alembic Setup

| # | Todo | Status | Time |
|---|---|---|---|
| 2.2.1 | Install `sqlalchemy[asyncio]` + `alembic` + `asyncpg` | ⬜ | 15 min |
| 2.2.2 | Create `database.py` (engine, session, base) | ⬜ | 1 jam |
| 2.2.3 | Initialize Alembic | ⬜ | 15 min |
| 2.2.4 | Configure `alembic.ini` + `env.py` | ⬜ | 30 min |
| 2.2.5 | Create initial migration (all 20 tables) | ⬜ | 2 jam |
| 2.2.6 | Run migration, verify tables created | ⬜ | 30 min |
| 2.2.7 | Test: insert + query via SQLAlchemy | ⬜ | 30 min |

**Definition of Done:** `alembic upgrade head` creates all tables.

---

#### Task 2.3: Dual-Write Layer

| # | Todo | Status | Time |
|---|---|---|---|
| 2.3.1 | Create `DualWriter` class | ⬜ | 1 jam |
| 2.3.2 | Implement `write(sqlite_fn, pg_fn)` | ⬜ | 1 jam |
| 2.3.3 | Implement `read(source='sqlite'/'pg'/'auto')` | ⬜ | 1 jam |
| 2.3.4 | Add health check for PostgreSQL | ⬜ | 30 min |
| 2.3.5 | Fallback to SQLite if PG unavailable | ⬜ | 1 jam |
| 2.3.6 | Test: write to both, read from both | ⬜ | 1 jam |

**Definition of Done:** Dual-write operational, fallback works.

---

### Phase 3: Data Migration (Minggu 4)

#### Task 3.1: Export SQLite Data

| # | Todo | Status | Time |
|---|---|---|---|
| 3.1.1 | Write export script for each .db file | ⬜ | 2 jam |
| 3.1.2 | Export all 30 files to JSON | ⬜ | 1 jam |
| 3.1.3 | Validate export completeness | ⬜ | 30 min |
| 3.1.4 | Backup exported data | ⬜ | 15 min |

**Definition of Done:** All data exported to JSON files.

---

#### Task 3.2: Transform & Import

| # | Todo | Status | Time |
|---|---|---|---|
| 3.2.1 | Write transform scripts (old schema → new schema) | ⬜ | 3 jam |
| 3.2.2 | Import organizations + users first | ⬜ | 1 jam |
| 3.2.3 | Import sessions + messages | ⬜ | 1 jam |
| 3.2.4 | Import tasks + notifications | ⬜ | 30 min |
| 3.2.5 | Import vault + memories | ⬜ | 1 jam |
| 3.2.6 | Import API keys + usage events | ⬜ | 30 min |
| 3.2.7 | Validate: row counts match | ⬜ | 30 min |

**Definition of Done:** All data in PostgreSQL, counts match SQLite.

---

#### Task 3.3: Switch Read Path

| # | Todo | Status | Time |
|---|---|---|---|
| 3.3.1 | Change `DualWriter.read(source='pg')` | ⬜ | 30 min |
| 3.3.2 | Monitor for errors (1-2 hari) | ⬜ | 2 hari |
| 3.3.3 | Compare response times (SQLite vs PG) | ⬜ | 1 jam |
| 3.3.4 | Keep SQLite as read-only fallback | ⬜ | 15 min |

**Definition of Done:** All reads from PostgreSQL, fallback available.

---

### Phase 4: pgvector + Semantic Search (Minggu 5-6)

#### Task 4.1: Embedding Pipeline

| # | Todo | Status | Time |
|---|---|---|---|
| 4.1.1 | Choose embedding model (local vs OpenAI) | ⬜ | 30 min |
| 4.1.2 | Install embedding library | ⬜ | 15 min |
| 4.1.3 | Implement `embed(text) → vector(768)` | ⬜ | 1 jam |
| 4.1.4 | Implement `batch_embed(texts) → vectors` | ⬜ | 1 jam |
| 4.1.5 | Test: embed sample texts, verify dimensions | ⬜ | 30 min |

**Definition of Done:** Embedding pipeline produces 768-dim vectors.

---

#### Task 4.2: Migrate Semantic Data

| # | Todo | Status | Time |
|---|---|---|---|
| 4.2.1 | Export semantic_search.db | ⬜ | 30 min |
| 4.2.2 | Generate embeddings for all entries | ⬜ | 2 jam |
| 4.2.3 | Import to `memories` table with vectors | ⬜ | 1 jam |
| 4.2.4 | Import to `semantic_index` table | ⬜ | 1 jam |
| 4.2.5 | Create IVFFlat indexes | ⬜ | 30 min |
| 4.2.6 | Test: vector similarity search | ⬜ | 1 jam |

**Definition of Done:** Semantic search returns relevant results.

---

#### Task 4.3: Hybrid Search

| # | Todo | Status | Time |
|---|---|---|---|
| 4.3.1 | Implement keyword search (PostgreSQL FTS) | ⬜ | 1 jam |
| 4.3.2 | Implement vector search (pgvector) | ⬜ | 1 jam |
| 4.3.3 | Implement hybrid scoring (keyword + vector) | ⬜ | 2 jam |
| 4.3.4 | Add `search_mode` parameter (keyword/vector/hybrid) | ⬜ | 30 min |
| 4.3.5 | Benchmark: <100ms for 100K vectors | ⬜ | 1 jam |
| 4.3.6 | Test: search returns relevant results | ⬜ | 1 jam |

**Definition of Done:** Hybrid search <100ms, relevant results.

---

### Phase 5: Cleanup (Minggu 7-8)

#### Task 5.1: Remove SQLite Dependencies

| # | Todo | Status | Time |
|---|---|---|---|
| 5.1.1 | Remove all `sqlite3.connect()` calls | ⬜ | 2 jam |
| 5.1.2 | Remove SQLite-specific code (PRAGMA, etc.) | ⬜ | 1 jam |
| 5.1.3 | Remove 30+ .db files from repo | ⬜ | 30 min |
| 5.1.4 | Update `.gitignore` | ⬜ | 15 min |
| 5.1.5 | Remove unused modules that depend on SQLite | ⬜ | 1 jam |

**Definition of Done:** Zero SQLite references in code.

---

#### Task 5.2: Update Tests

| # | Todo | Status | Time |
|---|---|---|---|
| 5.2.1 | Update test fixtures to use PostgreSQL | ⬜ | 2 jam |
| 5.2.2 | Add test database setup/teardown | ⬜ | 1 jam |
| 5.2.3 | Run full test suite | ⬜ | 1 jam |
| 5.2.4 | Fix failing tests | ⬜ | 2 jam |
| 5.2.5 | Verify: 614+ tests pass | ⬜ | 30 min |

**Definition of Done:** All tests pass with PostgreSQL.

---

#### Task 5.3: Documentation & Handoff

| # | Todo | Status | Time |
|---|---|---|---|
| 5.3.1 | Update README.md | ⬜ | 1 jam |
| 5.3.2 | Create `MIGRATION_GUIDE.md` | ⬜ | 2 jam |
| 5.3.3 | Update API docs | ⬜ | 1 jam |
| 5.3.4 | Create runbook for ops | ⬜ | 1 jam |
| 5.3.5 | Final review + commit | ⬜ | 1 jam |

**Definition of Done:** Documentation complete, repo clean.

---

## 📊 Summary

| Phase | Tasks | Todos | Est. Time |
|---|---|---|---|
| Phase 0: Stabilize | 3 | 12 | 1 hari |
| Phase 1: Auth | 4 | 24 | 2 hari |
| Phase 2: PG Setup | 3 | 18 | 2 hari |
| Phase 3: Migration | 3 | 21 | 2 hari |
| Phase 4: pgvector | 3 | 18 | 2 hari |
| Phase 5: Cleanup | 3 | 15 | 2 hari |
| **Total** | **19** | **108** | **11 hari** |

---

## 🔄 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 0          Phase 1          Phase 2          Phase 3      │
│  ┌──────┐        ┌──────┐        ┌──────┐        ┌──────┐      │
│  │Fix   │───────▶│Auth  │───────▶│PG    │───────▶│Data  │      │
│  │Bugs  │        │System│        │Setup │        │Migrate│      │
│  └──────┘        └──────┘        └──────┘        └──────┘      │
│       │              │              │              │             │
│       ▼              ▼              ▼              ▼             │
│  ┌──────┐        ┌──────┐        ┌──────┐        ┌──────┐      │
│  │Tests │        │Tests │        │Tests │        │Tests │      │
│  │Pass  │        │Pass  │        │Pass  │        │Pass  │      │
│  └──────┘        └──────┘        └──────┘        └──────┘      │
│       │              │              │              │             │
│       └──────────────┴──────────────┴──────────────┘             │
│                              │                                   │
│                              ▼                                   │
│                    Phase 4          Phase 5                      │
│                    ┌──────┐        ┌──────┐                      │
│                    │pgvector───────▶│Clean │                      │
│                    │Search│        │up    │                      │
│                    └──────┘        └──────┘                      │
│                         │              │                         │
│                         ▼              ▼                         │
│                    ┌──────┐        ┌──────┐                      │
│                    │Tests │        │Tests │                      │
│                    │Pass  │        │Pass  │                      │
│                    └──────┘        └──────┘                      │
│                                        │                         │
│                                        ▼                         │
│                                   ┌──────┐                      │
│                                   │DONE  │                      │
│                                   └──────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Approval

| Role | Name | Date | Signature |
|---|---|---|---|
| Author | Hermes (Aeryn System) | 2026-08-28 | ✅ |
| Reviewer | Sen | | |
| Approver | Sen | | |

---

*End of document.*
