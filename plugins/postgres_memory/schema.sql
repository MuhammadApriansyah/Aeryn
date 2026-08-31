-- Hermes PostgreSQL Memory Plugin — Schema
-- Run: psql -U sen -d sen -f schema.sql

-- Create schema
CREATE SCHEMA IF NOT EXISTS hermes;

-- Session summaries: compressed context per session
CREATE TABLE IF NOT EXISTS hermes.sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT UNIQUE NOT NULL,
    profile         TEXT NOT NULL DEFAULT 'default',
    title           TEXT,
    model           TEXT,
    provider        TEXT,
    source          TEXT,
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    message_count   INTEGER,
    tool_calls_count INTEGER,
    summary         TEXT,
    summary_vector  vector(384),
    project_dir     TEXT,
    branches        TEXT[],
    files_touched   TEXT[],
    entities        JSONB,
    tools_used      TEXT[],
    divisions_used  TEXT[],
    importance      FLOAT DEFAULT 0.5,
    access_count    INTEGER DEFAULT 0,
    last_accessed   TIMESTAMPTZ,
    tags            TEXT[],
    category        TEXT,
    transcript_compressed BYTEA,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Memory entries: granular facts/learnings
CREATE TABLE IF NOT EXISTS hermes.memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT REFERENCES hermes.sessions(session_id),
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    value_vector    vector(384),
    tier            TEXT NOT NULL DEFAULT 'warm',
    type            TEXT NOT NULL DEFAULT 'fact',
    source_type     TEXT,
    source_detail   TEXT,
    entities        JSONB,
    confidence      FLOAT DEFAULT 1.0,
    importance      FLOAT DEFAULT 0.5,
    decay_rate      FLOAT DEFAULT 0.01,
    last_reinforced TIMESTAMPTZ,
    access_count    INTEGER DEFAULT 0,
    last_accessed   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

-- Projects registry
CREATE TABLE IF NOT EXISTS hermes.projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    dir_path        TEXT,
    tech_stack      TEXT[],
    dependencies    JSONB,
    session_count   INTEGER DEFAULT 0,
    last_active     TIMESTAMPTZ,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences
CREATE TABLE IF NOT EXISTS hermes.preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             TEXT UNIQUE NOT NULL,
    value           JSONB NOT NULL,
    confidence      FLOAT DEFAULT 1.0,
    evidence_count  INTEGER DEFAULT 1,
    last_observed   TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Entity registry
CREATE TABLE IF NOT EXISTS hermes.entities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,
    aliases         TEXT[],
    metadata        JSONB,
    session_count   INTEGER DEFAULT 0,
    mention_count   INTEGER DEFAULT 0,
    last_mentioned  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, type)
);

-- Entity relationships
CREATE TABLE IF NOT EXISTS hermes.relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity   UUID REFERENCES hermes.entities(id),
    target_entity   UUID REFERENCES hermes.entities(id),
    relation_type   TEXT NOT NULL,
    strength        FLOAT DEFAULT 1.0,
    evidence        TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_entity, target_entity, relation_type)
);

-- Indexes
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
CREATE INDEX ON hermes.entities (type, name);
CREATE INDEX ON hermes.entities USING GIN (aliases);

-- Vector similarity indexes
CREATE INDEX ON hermes.sessions USING ivfflat (summary_vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON hermes.memories USING ivfflat (value_vector vector_cosine_ops) WITH (lists = 100);

-- Views
CREATE OR REPLACE VIEW hermes.active_memories AS
SELECT * FROM hermes.memories
WHERE expires_at IS NULL OR expires_at > NOW();

CREATE OR REPLACE VIEW hermes.recent_sessions AS
SELECT * FROM hermes.sessions
WHERE started_at > NOW() - INTERVAL '30 days'
ORDER BY importance DESC, started_at DESC;

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION hermes.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS hermes_sessions_updated_at ON hermes.sessions;
CREATE TRIGGER hermes_sessions_updated_at
    BEFORE UPDATE ON hermes.sessions
    FOR EACH ROW EXECUTE FUNCTION hermes.update_updated_at();

DROP TRIGGER IF EXISTS hermes_memories_updated_at ON hermes.memories;
CREATE TRIGGER hermes_memories_updated_at
    BEFORE UPDATE ON hermes.memories
    FOR EACH ROW EXECUTE FUNCTION hermes.update_updated_at();

-- Auto-save session summary (called by application)
CREATE OR REPLACE FUNCTION hermes.save_session_summary(
    p_session_id TEXT,
    p_summary TEXT,
    p_importance FLOAT DEFAULT 0.5,
    p_tags TEXT[] DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO hermes.sessions (session_id, summary, importance, tags, started_at, ended_at)
    VALUES (p_session_id, p_summary, p_importance, p_tags, NOW(), NOW())
    ON CONFLICT (session_id) DO UPDATE SET
        summary = EXCLUDED.summary,
        importance = EXCLUDED.importance,
        tags = EXCLUDED.tags,
        ended_at = NOW(),
        updated_at = NOW()
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Semantic search function
CREATE OR REPLACE FUNCTION hermes.search_memories(
    query_vector vector(384),
    limit_count INTEGER DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.3
) RETURNS TABLE(id UUID, key TEXT, value TEXT, similarity FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.key,
        m.value,
        1 - (m.value_vector <=> query_vector) AS similarity
    FROM hermes.memories m
    WHERE m.value_vector IS NOT NULL
    AND (m.expires_at IS NULL OR m.expires_at > NOW())
    AND 1 - (m.value_vector <=> query_vector) >= min_similarity
    ORDER BY m.value_vector <=> query_vector
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
