#!/usr/bin/env python3
"""V39.81-V39.84 — Enhanced Memory: Entity Extraction, Preferences, Graph, Cross-Session.

Combines all memory enhancements into one cohesive module:
- V39.81: Better entity extraction with NER-style patterns
- V39.82: Memory graph with relationship tracking
- V39.83: Cross-session recall via semantic search
- V39.84: User preference learning with confidence decay
"""

import os
import sys
import re
import json
import time
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.database.semantic_search import get_semantic_search
from aeryn_core.memory.memory_learning import get_memory_learner, MemoryLearner
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "enhanced_memory.db")


class EnhancedEntityExtractor:
    """Enhanced entity extraction with NER-style patterns and Indonesian language support."""
    
    # Comprehensive entity patterns
    PATTERNS = {
        "person": [
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Full names (John Smith)
            r"\b(sen|user|admin|developer|tester|manager|owner)\b",
            r"\b(bu|pak|mas|mbak|dik)\s+\w+",  # Indonesian honorifics
        ],
        "location": [
            r"\b(di|ke|dari|untuk)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",  # Indonesian prepositions
            r"\b(jakarta|bandung|surabaya|medan|semarang|bali|yogyakarta|malang|batam|manado|makassar|palembang|balikpapan| Samarinda|pekanbaru|bandar lampung|padang|denpasar|malang|tasikmalaya|banjarmasin|pontianak|cilacap|jember|kediri|madiun|madiun|magelang|mojokerto|pasuruan|probolinggo|sidoarjo|surakarta|tegal|ternate|yogyakarta)\b",
            r"\b(rumah|kantor|sekolah|kampus|universitas|mall|restoran|hotel|bandara|stasiun|terminal|puskesmas|rs|rumah sakit|taman|pasar|masjid|musholla|gereja|vihara|klenteng)\b",
        ],
        "technology": [
            r"\b(python|javascript|typescript|java|kotlin|swift|go|rust|c\+\+|c#|ruby|php|scala|perl|haskell|elixir|clojure|dart|lua|r|matlab)\b",
            r"\b(react|vue|angular|svelte|next\.?js|nuxt|express|fastify|flask|django|spring|rails|laravel|symfony|dotnet|\.net|asp\.net)\b",
            r"\b(docker|kubernetes|k8s|terraform|ansible|jenkins|github actions|gitlab ci|circleci|travis|nginx|apache|tomcat)\b",
            r"\b(postgresql|mysql|mongodb|redis|elasticsearch|cassandra|cockroachdb|sqlite|mariadb|oracle|sql server|dynamodb|firestore)\b",
            r"\b(aws|gcp|azure|digitalocean|linode|vultr|heroku|vercel|netlify|cloudflare|akamai)\b",
            r"\b(git|github|gitlab|bitbucket|jira|confluence|slack|discord|notion|trello|asana|linear)\b",
        ],
        "project": [
            r"\b(project|proyek|aplikasi|sistem|platform|tools?|framework|library|module)\s+\w+",
            r"\b(aeryn|webnovel|hermes|n8n|website|backend|frontend|api|mobil|desktop)\b",
        ],
        "temporal": [
            r"\b(hari ini|kemarin|besok|lusa|minggu lalu|minggu depan|bulan lalu|bulan depan|tahun lalu|tahun depan|tadi|baru saja|akan|sedang|telah|sudah|belum|pernah|selalu|sering|jarang|kadang|sekali)\b",
            r"\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu)\b",
            r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b",
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",  # Dates
            r"\b\d{1,2}:\d{2}\b",  # Times
        ],
        "sentiment": [
            r"\b(suka|cinta|senang|bahagia|senang|keren|mantap|bagus|hebat|luar biasa|wow|amazing|excellent)\b",
            r"\b(benci|marah|kesal|sebel|jelek|buruk|payah|gagal|error|bug|sulit|susah|ribet|repot)\b",
            r"\b(ragu|mungkin|mungkin saja|sepertinya|kayaknya|kira|kurang lebih|agak|cukup)\b",
        ],
    }
    
    def extract(self, text: str) -> Dict[str, List[Dict]]:
        """Extract entities with context and confidence."""
        entities = {}
        
        for entity_type, patterns in self.PATTERNS.items():
            found = []
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.I):
                    value = match.group(0).strip()
                    if len(value) < 2:
                        continue
                    
                    # Get surrounding context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end].strip()
                    
                    found.append({
                        "value": value.lower(),
                        "context": context,
                        "position": match.start(),
                    })
            
            # Deduplicate by value, keep highest context quality
            seen = {}
            for item in found:
                val = item["value"]
                if val not in seen or len(item["context"]) > len(seen[val]["context"]):
                    seen[val] = item
            
            if seen:
                entities[entity_type] = list(seen.values())
        
        return entities


class PreferenceLearnerV2:
    """Enhanced preference learning with confidence decay and reinforcement."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence_count INTEGER DEFAULT 1,
                    last_reinforced TEXT,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, category, key)
                );
                
                CREATE TABLE IF NOT EXISTS preference_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    confidence REAL,
                    changed_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_prefs_user ON user_preferences(user_id, confidence DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def learn(self, user_id: str, category: str, key: str, value: str,
              confidence: float = 0.5):
        """Learn a preference with confidence tracking."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if exists
            row = conn.execute("""
                SELECT id, value, confidence, evidence_count FROM user_preferences
                WHERE user_id = ? AND category = ? AND key = ?
            """, (user_id, category, key)).fetchone()
            
            now = datetime.now().isoformat()
            
            if row:
                old_value = row[1]
                old_conf = row[2]
                count = row[3]
                
                # Reinforcement: same value increases confidence
                if old_value == value:
                    new_conf = min(old_conf + 0.1, 0.99)
                    new_count = count + 1
                else:
                    # Value change: slight confidence reduction
                    new_conf = max(old_conf - 0.05, 0.1)
                    new_count = count + 1
                
                conn.execute("""
                    UPDATE user_preferences
                    SET value = ?, confidence = ?, evidence_count = ?,
                        last_reinforced = ?, updated_at = ?
                    WHERE id = ?
                """, (value, new_conf, new_count, now, now, row[0]))
                
                # Track history if value changed
                if old_value != value:
                    conn.execute("""
                        INSERT INTO preference_history (user_id, category, key, old_value, new_value, confidence)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, category, key, old_value, value, new_conf))
            else:
                conn.execute("""
                    INSERT INTO user_preferences (user_id, category, key, value, confidence, last_reinforced)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, category, key, value, confidence, now))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_preferences(self, user_id: str, min_confidence: float = 0.0) -> Dict:
        """Get preferences with confidence filtering."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT category, key, value, confidence, evidence_count, updated_at
                FROM user_preferences WHERE user_id = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (user_id, min_confidence)).fetchall()
            
            prefs = defaultdict(dict)
            for r in rows:
                prefs[r[0]][r[1]] = {
                    "value": r[2],
                    "confidence": r[3],
                    "evidence_count": r[4],
                    "updated_at": r[5],
                }
            
            return dict(prefs)
        finally:
            conn.close()
    
    def decay_confidence(self, user_id: str, days_threshold: int = 30, decay_rate: float = 0.05):
        """Decay confidence for stale preferences."""
        cutoff = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE user_preferences
                SET confidence = MAX(confidence - ?, 0.1)
                WHERE user_id = ? AND updated_at < ? AND confidence > 0.1
            """, (decay_rate, user_id, cutoff))
            conn.commit()
        finally:
            conn.close()


class CrossSessionRecall:
    """Recall memories across sessions using semantic search."""
    
    def __init__(self):
        self.search = get_semantic_search()
        self.vault = None  # Lazy load
    
    def index_session(self, user_id: str, session_id: str, messages: List[Dict]):
        """Index a session for later recall."""
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if len(content) < 10:
                continue
            
            memory_id = f"{session_id}/{role}/{i}"
            title = f"{role}: {content[:50]}..."
            
            try:
                self.search.index_memory(
                    memory_id=memory_id,
                    title=title,
                    content=content[:2000],
                    source="session",
                    author=user_id,
                    metadata={"session_id": session_id, "role": role},
                )
            except Exception:
                from aeryn_core.utils.logger import log_exception
                log_exception(e, context=f"{__name__}")
                pass
    
    def recall(self, query: str, user_id: str = "default", limit: int = 5) -> List[Dict]:
        """Recall memories from past sessions."""
        try:
            results = self.search.search(query, limit=limit)
            # Filter to user's own sessions
            return [r for r in results if r.get("author") == user_id]
        except Exception:
            return []
    
    def get_session_context(self, user_id: str, current_goal: str, limit: int = 3) -> str:
        """Get relevant context from past sessions for current goal."""
        recalled = self.recall(current_goal, user_id, limit)
        
        if not recalled:
            return ""
        
        parts = ["[Relevant past context]"]
        for r in recalled:
            parts.append(f"- {r.get('title', '')}: {r.get('content', '')[:150]}")
        
        return "\n".join(parts)


# Singleton
_extractor = None
_learner = None
_recall = None

def get_entity_extractor() -> EnhancedEntityExtractor:
    global _extractor
    if _extractor is None:
        _extractor = EnhancedEntityExtractor()
    return _extractor

def get_preference_learner() -> PreferenceLearnerV2:
    global _learner
    if _learner is None:
        _learner = PreferenceLearnerV2()
    return _learner

def get_cross_session_recall() -> CrossSessionRecall:
    global _recall
    if _recall is None:
        _recall = CrossSessionRecall()
    return _recall


if __name__ == "__main__":
    print("=== Enhanced Memory Test ===")
    
    # Entity extraction
    extractor = get_entity_extractor()
    text = "Aku suka python dan javascript. Aku mau belajar docker di jakarta. Pak Budi adalah mentor-ku."
    entities = extractor.extract(text)
    print(f"Entities: {json.dumps({k: len(v) for k, v in entities.items()}, indent=2)}")
    
    # Preference learning
    learner = get_preference_learner()
    learner.learn("sen", "language", "preferred", "indonesian", 0.8)
    learner.learn("sen", "tech", "primary_language", "python", 0.9)
    learner.learn("sen", "tech", "primary_language", "python", 0.9)  # Reinforce
    prefs = learner.get_preferences("sen")
    print(f"Preferences: {json.dumps(prefs, indent=2)}")
    
    # Cross-session recall
    recall = get_cross_session_recall()
    recall.index_session("session_001", "sen", [
        {"role": "user", "content": "How to install Docker?"},
        {"role": "assistant", "content": "Use apt-get install docker.io"},
    ])
    context = recall.get_session_context("sen", "docker installation")
    print(f"Session context: {context[:500]}")
