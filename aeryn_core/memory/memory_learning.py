#!/usr/bin/env python3
"""V39.77 — Memory Learning: Mem0-style entity extraction + preference learning.

Aeryn learns from interactions:
- Extracts entities (people, places, concepts)
- Learns user preferences over time
- Builds semantic memory graph
- Cross-session recall improvement
"""

import os
import sys
import re
import json
import time
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "memory_learning.db")


class EntityExtractor:
    """Extract entities from text."""
    
    PATTERNS = {
        "person": [
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Full names
            r"\b(sen|user|admin|developer|tester)\b",  # Names/roles
        ],
        "location": [
            r"\b(di|ke|dari) ([A-Z][a-z]+)\b",  # Indonesian prepositions + place
            r"\b(jakarta|bandung|surabaya|bali|indonesia|jaksel|jakut|jakbar|jaktim)\b",
            r"\b(rumah|kantor|sekolah|universitas|mall|hotel|bandara)\b",
        ],
        "technology": [
            r"\b(python|javascript|react|vue|docker|kubernetes|linux|git|sql|nosql)\b",
            r"\b(fastify|flask|django|express|nextjs|nuxt|svelte|angular)\b",
            r"\b(aws|gcp|azure|vercel|netlify|heroku|cloudflare)\b",
        ],
        "project": [
            r"\b(aeryn|webnovel|hermes|n8n)\b",
            r"\b(project|proyek|aplikasi|sistem|platform|tools?)\b",
        ],
        "temporal": [
            r"\b(hari ini|kemarin|besok|lalu|minggu|bulan|tahun|jam|menit)\b",
            r"\b(senin|selasa|rabu|kamis|jumat|sabtu|minggu)\b",
            r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b",
        ],
    }
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities by type."""
        entities = {}
        
        for entity_type, patterns in self.PATTERNS.items():
            found = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.I)
                if matches:
                    if isinstance(matches[0], tuple):
                        # Take last group if tuple
                        found.extend([m[-1] if isinstance(m, tuple) else m for m in matches])
                    else:
                        found.extend(matches)
            
            # Deduplicate
            found = list(set(f.lower() for f in found))
            if found:
                entities[entity_type] = found
        
        return entities


class PreferenceLearner:
    """Learn user preferences from interactions."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence_count INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_profile (
                    user_id TEXT PRIMARY KEY,
                    name TEXT DEFAULT '',
                    language TEXT DEFAULT 'indonesian',
                    style TEXT DEFAULT 'casual',
                    interests TEXT DEFAULT '[]',
                    last_active TEXT,
                    interaction_count INTEGER DEFAULT 0,
                    preferences_json TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS memory_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    related_to TEXT,
                    relationship TEXT,
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_prefs_user ON preferences(user_id, category, key);
                CREATE INDEX IF NOT EXISTS idx_graph_entity ON memory_graph(entity, entity_type);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def learn_preference(self, user_id: str, category: str, key: str, value: str,
                         confidence: float = 0.5):
        """Learn a new preference or update existing."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if preference exists
            row = conn.execute("""
                SELECT id, confidence, evidence_count FROM preferences
                WHERE user_id = ? AND category = ? AND key = ?
            """, (user_id, category.lower(), key.lower())).fetchone()
            
            if row:
                # Update with exponential moving average
                old_conf = row[1]
                count = row[2]
                new_conf = old_conf + (confidence - old_conf) / (count + 1)
                
                conn.execute("""
                    UPDATE preferences
                    SET value = ?, confidence = ?, evidence_count = evidence_count + 1, updated_at = ?
                    WHERE id = ?
                """, (value, new_conf, datetime.now().isoformat(), row[0]))
            else:
                conn.execute("""
                    INSERT INTO preferences (user_id, category, key, value, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, category.lower(), key.lower(), value, confidence))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_preferences(self, user_id: str, category: str = None) -> Dict:
        """Get all preferences for a user."""
        conn = sqlite3.connect(self.db_path)
        try:
            if category:
                rows = conn.execute("""
                    SELECT key, value, confidence FROM preferences
                    WHERE user_id = ? AND category = ? ORDER BY confidence DESC
                """, (user_id, category.lower())).fetchall()
            else:
                rows = conn.execute("""
                    SELECT category, key, value, confidence FROM preferences
                    WHERE user_id = ? ORDER BY category, confidence DESC
                """, (user_id,)).fetchall()
            
            if category:
                return {r[0]: {"value": r[1], "confidence": r[2]} for r in rows}
            else:
                prefs = {}
                for r in rows:
                    if r[0] not in prefs:
                        prefs[r[0]] = {}
                    prefs[r[0]][r[1]] = {"value": r[2], "confidence": r[3]}
                return prefs
        finally:
            conn.close()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT user_id, name, language, style, interests, last_active, interaction_count, preferences_json
                FROM user_profile WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if row:
                return {
                    "user_id": row[0], "name": row[1], "language": row[2],
                    "style": row[3], "interests": json.loads(row[4]) if row[4] else [],
                    "last_active": row[5], "interaction_count": row[6],
                    "preferences": json.loads(row[7]) if row[7] else {}
                }
            return None
        finally:
            conn.close()
    
    def update_user_profile(self, user_id: str, **kwargs):
        """Update user profile."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if exists
            row = conn.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
            
            if row:
                updates = []
                params = []
                for key, value in kwargs.items():
                    updates.append(f"{key} = ?")
                    if isinstance(value, (list, dict)):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)
                params.append(user_id)
                
                conn.execute(f"""
                    UPDATE user_profile SET {', '.join(updates)} WHERE user_id = ?
                """, params)
            else:
                conn.execute("""
                    INSERT INTO user_profile (user_id, name, language, style, interests)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, kwargs.get("name", ""), kwargs.get("language", "indonesian"),
                      kwargs.get("style", "casual"), json.dumps(kwargs.get("interests", []))))
            
            conn.commit()
        finally:
            conn.close()
    
    def add_to_memory_graph(self, entity: str, entity_type: str,
                            related_to: str = None, relationship: str = None,
                            context: str = ""):
        """Add an entity to the memory graph."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO memory_graph (entity, entity_type, related_to, relationship, context)
                VALUES (?, ?, ?, ?, ?)
            """, (entity.lower(), entity_type, related_to, relationship, context))
            conn.commit()
        finally:
            conn.close()
    
    def get_memory_graph(self, entity: str = None, entity_type: str = None,
                         limit: int = 20) -> List[Dict]:
        """Query the memory graph."""
        conn = sqlite3.connect(self.db_path)
        try:
            if entity:
                rows = conn.execute("""
                    SELECT entity, entity_type, related_to, relationship, context
                    FROM memory_graph WHERE entity = ? OR related_to = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (entity.lower(), entity.lower(), limit)).fetchall()
            elif entity_type:
                rows = conn.execute("""
                    SELECT entity, entity_type, related_to, relationship, context
                    FROM memory_graph WHERE entity_type = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (entity_type, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT entity, entity_type, related_to, relationship, context
                    FROM memory_graph ORDER BY created_at DESC LIMIT ?
                """, (limit,)).fetchall()
            
            return [
                {
                    "entity": r[0], "type": r[1], "related_to": r[2],
                    "relationship": r[3], "context": r[4]
                }
                for r in rows
            ]
        finally:
            conn.close()


class MemoryLearner:
    """Orchestrates memory learning from interactions."""
    
    def __init__(self):
        self.extractor = EntityExtractor()
        self.learner = PreferenceLearner()
    
    def process_interaction(self, user_id: str, user_message: str,
                            bot_response: str = ""):
        """Process an interaction and learn from it."""
        # Extract entities from both user message and bot response
        user_entities = self.extractor.extract(user_message)
        bot_entities = self.extractor.extract(bot_response)
        
        all_entities = {**user_entities}
        for key, values in bot_entities.items():
            if key in all_entities:
                all_entities[key] = list(set(all_entities[key] + values))
            else:
                all_entities[key] = values
        
        # Update user profile
        profile = self.learner.get_user_profile(user_id)
        if profile is None:
            self.learner.update_user_profile(user_id, interaction_count=1)
        else:
            self.learner.update_user_profile(
                user_id,
                interaction_count=profile.get("interaction_count", 0) + 1,
                last_active=datetime.now().isoformat()
            )
        
        # Learn preferences
        self._infer_preferences(user_id, user_message, user_entities)
        
        # Update memory graph
        self._update_memory_graph(user_id, all_entities, user_message)
        
        return {
            "entities": all_entities,
            "profile_updated": True,
            "preferences_learned": len(all_entities),
        }
    
    def _infer_preferences(self, user_id: str, text: str, entities: Dict):
        """Infer preferences from text."""
        text_lower = text.lower()
        
        # Language preference
        if any(w in text_lower for w in ["indonesia", "bahasa", "aku", "kamu", "saya"]):
            self.learner.learn_preference(user_id, "communication", "language", "indonesian", 0.8)
        
        if any(w in text_lower for w in ["english", "you", "i want", "please", "thanks"]):
            self.learner.learn_preference(user_id, "communication", "language", "english", 0.8)
        
        # Style preference
        if any(w in text_lower for w in ["tolong", "mohon", "bantu", "help"]):
            self.learner.learn_preference(user_id, "communication", "style", "formal", 0.6)
        
        if any(w in text_lower for w in ["yo", "hey", "hi", "bro", "bang", "cuy"]):
            self.learner.learn_preference(user_id, "communication", "style", "casual", 0.7)
        
        # Technology interests
        if "technology" in entities:
            for tech in entities["technology"]:
                self.learner.learn_preference(user_id, "interests", "technology", tech, 0.7)
        
        # Project interests
        if "project" in entities:
            for proj in entities["project"]:
                self.learner.learn_preference(user_id, "interests", "project", proj, 0.6)
    
    def _update_memory_graph(self, user_id: str, entities: Dict, context: str):
        """Update memory graph with extracted entities."""
        for entity_type, values in entities.items():
            for value in values:
                self.learner.add_to_memory_graph(
                    entity=value,
                    entity_type=entity_type,
                    related_to=user_id,
                    relationship="mentioned_by",
                    context=context[:200]
                )
    
    def get_user_context(self, user_id: str) -> Dict:
        """Get full user context (profile + preferences + memory)."""
        profile = self.learner.get_user_profile(user_id)
        preferences = self.learner.get_preferences(user_id)
        memory = self.learner.get_memory_graph(limit=10)
        
        return {
            "profile": profile,
            "preferences": preferences,
            "recent_memory": memory,
        }


# Singleton
_learner = None

def get_memory_learner() -> MemoryLearner:
    global _learner
    if _learner is None:
        _learner = MemoryLearner()
    return _learner


if __name__ == "__main__":
    learner = MemoryLearner()
    
    print("=== Memory Learning Test ===")
    
    # Process an interaction
    result = learner.process_interaction(
        user_id="sen",
        user_message="Aku suka python dan javascript. Aku mau belajar docker.",
        bot_response="Docker itu bagus untuk deployment!"
    )
    
    print(f"Entities: {json.dumps(result['entities'], indent=2, ensure_ascii=False)}")
    
    # Get user context
    context = learner.get_user_context("sen")
    print(f"\nUser Profile: {json.dumps(context['profile'], indent=2, ensure_ascii=False)}")
    print(f"Preferences: {json.dumps(context['preferences'], indent=2, ensure_ascii=False)}")
    print(f"Memory: {json.dumps(context['recent_memory'], indent=2, ensure_ascii=False)}")
