"""PostgreSQL Memory Plugin — Auto-save/load session context to PostgreSQL."""
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import asyncpg
import numpy as np

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────

class PostgresMemoryConfig:
    """Load config from environment or defaults."""
    
    def __init__(self):
        self.host = os.environ.get("POSTGRES_HOST", "localhost")
        self.port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.database = os.environ.get("POSTGRES_DB", "sen")
        self.user = os.environ.get("POSTGRES_USER", "sen")
        self.password = os.environ.get("POSTGRES_PASSWORD", "")
        self.ssl = os.environ.get("POSTGRES_SSL", "false").lower() == "true"
        self.pool_size = int(os.environ.get("POSTGRES_POOL_SIZE", "5"))
        self.schema = "hermes"
        
        # Embedding
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_device = os.environ.get("EMBEDDING_DEVICE", "cpu")
        
        # Lifecycle
        self.hot_days = int(os.environ.get("MEMORY_HOT_DAYS", "7"))
        self.warm_days = int(os.environ.get("MEMORY_WARM_DAYS", "30"))
        self.cold_days = int(os.environ.get("MEMORY_COLD_DAYS", "90"))
        self.decay_enabled = os.environ.get("MEMORY_DECAY", "true").lower() == "true"
        self.decay_rate = float(os.environ.get("MEMORY_DECAY_RATE", "0.01"))
        
        # Auto-save
        self.auto_save_enabled = True
        self.idle_minutes = 5
        self.min_messages = 10
        
        # Auto-load
        self.auto_load_enabled = True
        self.max_context_chars = 2000
        self.min_relevance = 0.3
        self.max_memories = 10


# ─── Embedding Engine ────────────────────────────────────────

class EmbeddingEngine:
    """Generate text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
    
    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback")
                self._model = None
    
    def embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text."""
        self._load_model()
        if self._model is None:
            return None
        try:
            vec = self._model.encode(text, show_progress_bar=False)
            return vec.tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        if self._model is None:
            return [None] * len(texts)
        try:
            vecs = self._model.encode(texts, show_progress_bar=False)
            return [v.tolist() for v in vecs]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [None] * len(texts)


# ─── PostgreSQL Memory Plugin ────────────────────────────────

class PostgresMemoryPlugin:
    """Main plugin class for PostgreSQL-backed memory."""
    
    def __init__(self, config: PostgresMemoryConfig = None):
        self.config = config or PostgresMemoryConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self.embedder = EmbeddingEngine(
            self.config.embedding_model,
            self.config.embedding_device
        )
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
    
    async def initialize(self):
        """Create connection pool."""
        if self.pool is None:
            dsn = f"postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            self.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=self.config.pool_size)
            logger.info(f"PostgreSQL pool created: {self.config.host}:{self.config.port}/{self.config.database}")
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    # ── Session Management ──
    
    async def save_session(self, session_id: str, summary: str, 
                          importance: float = 0.5, tags: List[str] = None,
                          metadata: Dict = None) -> str:
        """Save session summary to PostgreSQL."""
        await self.initialize()
        
        # Generate embedding
        summary_vec = self.embedder.embed(summary)
        vec_str = f"[{','.join(str(x) for x in summary_vec)}]" if summary_vec else None
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO hermes.sessions 
                    (session_id, summary, summary_vector, importance, tags, 
                     started_at, ended_at, message_count, tool_calls_count,
                     project_dir, files_touched, tools_used, divisions_used)
                VALUES ($1, $2, $3::vector, $4, $5, NOW(), NOW(), $6, $7, $8, $9, $10, $11)
                ON CONFLICT (session_id) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    summary_vector = EXCLUDED.summary_vector,
                    importance = EXCLUDED.importance,
                    tags = EXCLUDED.tags,
                    ended_at = NOW(),
                    updated_at = NOW()
                RETURNING id
            """, session_id, summary, vec_str, importance, tags or [],
                metadata.get("message_count", 0) if metadata else 0,
                metadata.get("tool_calls_count", 0) if metadata else 0,
                metadata.get("project_dir") if metadata else None,
                metadata.get("files_touched") if metadata else None,
                metadata.get("tools_used") if metadata else None,
                metadata.get("divisions_used") if metadata else None)
            
            return str(row["id"]) if row else None
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        await self.initialize()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM hermes.sessions WHERE session_id = $1", session_id)
            return dict(row) if row else None
    
    async def search_sessions(self, query: str, limit: int = 5) -> List[Dict]:
        """Search sessions by semantic similarity."""
        await self.initialize()
        query_vec = self.embedder.embed(query)
        if not query_vec:
            return []
        
        vec_str = f"[{','.join(str(x) for x in query_vec)}]"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT session_id, title, summary, importance, started_at,
                    1 - (summary_vector <=> $1::vector) AS similarity
                FROM hermes.sessions
                WHERE summary_vector IS NOT NULL
                AND started_at > NOW() - INTERVAL '90 days'
                ORDER BY summary_vector <=> $1::vector
                LIMIT $2
            """, vec_str, limit)
            
            return [dict(r) for r in rows]
    
    # ── Memory Management ──
    
    async def remember(self, key: str, value: str, 
                      memory_type: str = "fact",
                      importance: float = 0.5,
                      session_id: str = None,
                      entities: Dict = None,
                      ttl_days: int = None,
                      skip_embedding: bool = True) -> str:
        """Store a memory entry."""
        await self.initialize()
        
        # Generate embedding (optional for speed)
        vec_str = None
        if not skip_embedding:
            value_vec = self.embedder.embed(value)
            if value_vec:
                vec_str = f"[{','.join(str(x) for x in value_vec)}]"
        
        # Calculate tier
        tier = "hot" if importance > 0.7 else "warm" if importance > 0.3 else "cold"
        
        # Calculate expiry
        expires_at = None
        if ttl_days:
            expires_at = datetime.now() + timedelta(days=ttl_days)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO hermes.memories 
                    (session_id, key, value, value_vector, tier, type,
                     importance, entities, expires_at, source_type)
                VALUES ($1, $2, $3, $4::vector, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    value_vector = EXCLUDED.value_vector,
                    tier = EXCLUDED.tier,
                    importance = EXCLUDED.importance,
                    access_count = hermes.memories.access_count + 1,
                    last_accessed = NOW()
                RETURNING id
            """, session_id, key, value, vec_str, tier, memory_type,
                importance, json.dumps(entities) if entities else None,
                expires_at, "session")
            
            return str(row["id"]) if row else None
    
    async def recall(self, query: str, limit: int = 10, 
                     min_relevance: float = 0.3) -> List[Dict]:
        """Semantic search across memories."""
        await self.initialize()
        
        # Check cache
        cache_key = f"recall:{query}:{limit}"
        if cache_key in self._cache:
            if datetime.now() < self._cache_ttl.get(cache_key, datetime.min):
                return self._cache[cache_key]
        
        query_vec = self.embedder.embed(query)
        if not query_vec:
            return []
        
        vec_str = f"[{','.join(str(x) for x in query_vec)}]"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT key, value, type, tier, importance,
                    1 - (value_vector <=> $1::vector) AS similarity
                FROM hermes.memories
                WHERE value_vector IS NOT NULL
                AND (expires_at IS NULL OR expires_at > NOW())
                AND 1 - (value_vector <=> $1::vector) >= $2
                ORDER BY value_vector <=> $1::vector
                LIMIT $3
            """, vec_str, min_relevance, limit)
            
            results = [dict(r) for r in rows]
            
            # Update access stats
            for r in results:
                await conn.execute("""
                    UPDATE hermes.memories 
                    SET access_count = access_count + 1, last_accessed = NOW()
                    WHERE key = $1
                """, r["key"])
            
            # Cache results
            self._cache[cache_key] = results
            self._cache_ttl[cache_key] = datetime.now() + timedelta(minutes=5)
            
            return results
    
    async def forget(self, key: str) -> bool:
        """Remove a memory."""
        await self.initialize()
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM hermes.memories WHERE key = $1", key)
            return "DELETE 1" in result
    
    async def index_unindexed(self) -> int:
        """Generate embeddings for memories without vectors. Call periodically."""
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, value FROM hermes.memories 
                WHERE value_vector IS NULL
                LIMIT 100
            """)
            
            if not rows:
                return 0
            
            count = 0
            for row in rows:
                vec = self.embedder.embed(row["value"])
                if vec:
                    vec_str = f"[{','.join(str(x) for x in vec)}]"
                    await conn.execute("""
                        UPDATE hermes.memories 
                        SET value_vector = $1::vector
                        WHERE id = $2
                    """, vec_str, row["id"])
                    count += 1
            
            return count
    
    # ── Lifecycle ──
    
    async def decay_step(self):
        """Apply decay to all memories. Run periodically."""
        if not self.config.decay_enabled:
            return
        
        await self.initialize()
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE hermes.memories
                SET importance = GREATEST(0, importance - decay_rate)
                WHERE decay_rate > 0
            """)
            
            # Prune low-importance memories
            await conn.execute("""
                DELETE FROM hermes.memories
                WHERE importance < 0.05
                AND created_at < NOW() - INTERVAL '30 days'
            """)
            
            # Update tiers
            await conn.execute("""
                UPDATE hermes.memories SET tier = 'warm'
                WHERE tier = 'hot' AND created_at < NOW() - INTERVAL '%s days'
            """ % self.config.hot_days)
            
            await conn.execute("""
                UPDATE hermes.memories SET tier = 'cold'
                WHERE tier = 'warm' AND created_at < NOW() - INTERVAL '%s days'
            """ % self.config.warm_days)
    
    async def get_stats(self) -> Dict:
        """Get plugin statistics."""
        await self.initialize()
        async with self.pool.acquire() as conn:
            stats = {}
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.sessions")
            stats["total_sessions"] = row["cnt"]
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.memories")
            stats["total_memories"] = row["cnt"]
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.memories WHERE tier = 'hot'")
            stats["hot_memories"] = row["cnt"]
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.memories WHERE tier = 'warm'")
            stats["warm_memories"] = row["cnt"]
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.memories WHERE tier = 'cold'")
            stats["cold_memories"] = row["cnt"]
            
            row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM hermes.entities")
            stats["total_entities"] = row["cnt"]
            
            return stats


# ─── Singleton ──────────────────────────────────────────────

_plugin: Optional[PostgresMemoryPlugin] = None

def get_postgres_memory() -> PostgresMemoryPlugin:
    """Get or create plugin singleton."""
    global _plugin
    if _plugin is None:
        _plugin = PostgresMemoryPlugin()
    return _plugin
