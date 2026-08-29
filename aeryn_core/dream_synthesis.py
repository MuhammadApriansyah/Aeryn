#!/usr/bin/env python3
"""V39.80 — Dream Synthesis: Generate insights from memory patterns.

Inspired by Mem0's Dream feature. Analyzes stored memories to:
- Discover patterns and themes across sessions
- Generate insights not obvious from individual memories
- Identify user behavior changes over time
- Surface forgotten but relevant information
- Create "memory summaries" for different time periods
"""

import os
import sys
import json
import time
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.semantic_search import get_semantic_search
from aeryn_core.vault import AerynVault, LAYER_DAILY
from aeryn_core.social_memory import SocialMemory
from aeryn_core.shared_db import get_shared_db
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "dream_synthesis.db")


class DreamSynthesizer:
    """Generate insights from memory patterns."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize dream synthesis database."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS insights (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    insight_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    status TEXT DEFAULT 'active'
                );
                
                CREATE TABLE IF NOT EXISTS synthesis_runs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    run_type TEXT NOT NULL,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    insights_generated INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running'
                );
                
                CREATE INDEX IF NOT EXISTS idx_insights_user ON insights(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type, confidence DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def synthesize(self, user_id: str = "default", days: int = 7) -> Dict:
        """Run dream synthesis for a user."""
        import uuid
        run_id = str(uuid.uuid4())[:8]
        
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO synthesis_runs (id, user_id, run_type, status)
                VALUES (?, ?, 'dream', 'running')
            """, (run_id, user_id))
            conn.commit()
        finally:
            conn.close()
        
        insights = []
        
        # 1. Pattern Discovery
        patterns = self._discover_patterns(user_id, days)
        for pattern in patterns:
            stored = self._store_insight(user_id, "pattern", pattern)
            insights.append(stored)
        
        # 2. Theme Extraction
        themes = self._extract_themes(user_id, days)
        for theme in themes:
            stored = self._store_insight(user_id, "theme", theme)
            insights.append(stored)
        
        # 3. Behavior Change Detection
        changes = self._detect_changes(user_id, days)
        for change in changes:
            stored = self._store_insight(user_id, "behavior_change", change)
            insights.append(stored)
        
        # 4. Forgotten Memory Surfacing
        forgotten = self._surface_forgotten(user_id, days)
        for item in forgotten:
            stored = self._store_insight(user_id, "forgotten", item)
            insights.append(stored)
        
        # 5. Connection Discovery
        connections = self._discover_connections(user_id, days)
        for conn_item in connections:
            stored = self._store_insight(user_id, "connection", conn_item)
            insights.append(stored)
        
        # Mark synthesis complete
        duration = time.time() - start_time
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE synthesis_runs 
                SET status = 'completed', completed_at = ?, insights_generated = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), len(insights), run_id))
            conn.commit()
        finally:
            conn.close()
        
        return {
            "run_id": run_id,
            "user_id": user_id,
            "days_analyzed": days,
            "insights_generated": len(insights),
            "duration_seconds": round(duration, 2),
            "insights": [{"id": i["id"], "type": i["type"], "title": i["title"]} for i in insights[:10]],
        }
    
    def _discover_patterns(self, user_id: str, days: int) -> List[Dict]:
        """Discover recurring patterns in user behavior and topics."""
        patterns = []
        
        # Analyze social memory facts
        sm = SocialMemory()
        facts = sm.get_facts(user_id)
        
        if not facts:
            return patterns
        
        # Find repeated keywords/topics
        all_text = " ".join(str(f) for f in facts).lower()
        words = [w for w in all_text.split() if len(w) > 3]
        word_counts = Counter(words)
        
        # Find patterns (words that appear frequently)
        for word, count in word_counts.most_common(5):
            if count >= 2:
                patterns.append({
                    "title": f"Recurring pattern: '{word}'",
                    "content": f"The topic '{word}' has appeared {count} times in your memories. This seems to be something you think about regularly.",
                    "confidence": min(0.5 + count * 0.1, 0.95),
                    "evidence": [f"Mentioned {count} times"],
                })
        
        return patterns
    
    def _extract_themes(self, user_id: str, days: int) -> List[Dict]:
        """Extract major themes from recent memories."""
        themes = []
        
        # Analyze vault entries from the period
        vault = AerynVault()
        
        # Get recent daily entries
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            entries = vault.search(date, layer=LAYER_DAILY, limit=5)
            
            for entry in entries:
                preview = entry.get("preview", "")
                if len(preview) > 50:
                    themes.append({
                        "title": f"Daily reflection theme: {date}",
                        "content": f"On {date}, you were thinking about: {preview[:200]}...",
                        "confidence": 0.6,
                        "evidence": [f"Vault entry: {entry.get('path', '')}"],
                    })
        
        return themes[:5]  # Limit to top 5 themes
    
    def _detect_changes(self, user_id: str, days: int) -> List[Dict]:
        """Detect changes in user behavior or interests over time."""
        changes = []
        
        # Compare recent vs older preferences
        conn_local = sqlite3.connect(os.path.join(DATABASE_DIR, "memory_learning.db"))
        try:
            # Get preferences from different time periods
            recent = conn_local.execute("""
                SELECT key, value, confidence FROM preferences
                WHERE user_id = ? AND updated_at >= datetime('now', '-7 days')
                ORDER BY confidence DESC
            """, (user_id,)).fetchall()
            
            older = conn_local.execute("""
                SELECT key, value, confidence FROM preferences
                WHERE user_id = ? AND updated_at < datetime('now', '-7 days')
                ORDER BY confidence DESC
            """, (user_id,)).fetchall()
            
            recent_keys = {r[0]: r[1] for r in recent}
            older_keys = {o[0]: o[1] for o in older}
            
            # Find new preferences
            for key, value in recent_keys.items():
                if key not in older_keys:
                    changes.append({
                        "title": f"New interest detected: {key}",
                        "content": f"You've recently shown interest in '{key}' (value: {value}). This is a new preference that wasn't present before.",
                        "confidence": 0.7,
                        "evidence": [f"New preference: {key} = {value}"],
                    })
                elif older_keys[key] != value:
                    changes.append({
                        "title": f"Changed preference: {key}",
                        "content": f"Your preference for '{key}' changed from '{older_keys[key]}' to '{value}'.",
                        "confidence": 0.8,
                        "evidence": [f"Old: {older_keys[key]}", f"New: {value}"],
                    })
        except Exception:
            pass
        finally:
            conn_local.close()
        
        return changes
    
    def _surface_forgotten(self, user_id: str, days: int) -> List[Dict]:
        """Surface memories that may have been forgotten but are still relevant."""
        forgotten = []
        
        # Search for old memories that match recent topics
        search = get_semantic_search()
        
        # Get recent topics
        vault = AerynVault()
        recent_entries = vault.search("", layer=LAYER_DAILY, limit=10)
        
        if recent_entries:
            recent_topics = " ".join(e.get("preview", "")[:100] for e in recent_entries)
            
            # Search old memories related to recent topics
            try:
                old_memories = search.search(recent_topics[:200], limit=5)
                for mem in old_memories:
                    if mem.get("source") == "vault":
                        forgotten.append({
                            "title": f"Related memory: {mem.get('title', 'Unknown')[:50]}",
                            "content": f"This older memory seems relevant to your recent thoughts: {mem.get('content', '')[:300]}",
                            "confidence": mem.get("score", 0.5),
                            "evidence": [f"Memory: {mem.get('memory_id', '')}"],
                        })
            except Exception:
                pass
        
        return forgotten[:3]
    
    def _discover_connections(self, user_id: str, days: int) -> List[Dict]:
        """Discover connections between different memories."""
        connections = []
        
        # Use graph memory to find related entities
        try:
            from aeryn_core.graph_memory import get_graph_memory
            gm = get_graph_memory()
            
            # Find entities with many connections
            stats = gm.get_stats()
            if stats.get("nodes", 0) > 5:
                connections.append({
                    "title": f"Knowledge graph has {stats['nodes']} nodes and {stats['edges']} edges",
                    "content": f"Your knowledge graph shows {stats['nodes']} interconnected entities with {stats['edges']} relationships. This indicates a rich knowledge base.",
                    "confidence": 0.9,
                    "evidence": [f"Graph stats: {json.dumps(stats)}"],
                })
        except Exception:
            pass
        
        return connections
    
    def _store_insight(self, user_id: str, insight_type: str, insight_data: Dict) -> Dict:
        """Store a generated insight."""
        import uuid
        insight_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO insights (id, user_id, insight_type, title, content, confidence, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                insight_id,
                user_id,
                insight_type,
                insight_data.get("title", ""),
                insight_data.get("content", ""),
                insight_data.get("confidence", 0.5),
                json.dumps(insight_data.get("evidence", [])),
            ))
            conn.commit()
        finally:
            conn.close()
        
        return {
            "id": insight_id,
            "user_id": user_id,
            "type": insight_type,
            "title": insight_data.get("title", ""),
            "confidence": insight_data.get("confidence", 0.5),
        }
    
    def get_insights(self, user_id: str, limit: int = 20, insight_type: str = None) -> List[Dict]:
        """Get insights for a user."""
        conn = sqlite3.connect(self.db_path)
        try:
            if insight_type:
                rows = conn.execute("""
                    SELECT id, insight_type, title, content, confidence, evidence, created_at
                    FROM insights WHERE user_id = ? AND insight_type = ? AND status = 'active'
                    ORDER BY confidence DESC, created_at DESC LIMIT ?
                """, (user_id, insight_type, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, insight_type, title, content, confidence, evidence, created_at
                    FROM insights WHERE user_id = ? AND status = 'active'
                    ORDER BY confidence DESC, created_at DESC LIMIT ?
                """, (user_id, limit)).fetchall()
            
            return [
                {
                    "id": r[0],
                    "type": r[1],
                    "title": r[2],
                    "content": r[3],
                    "confidence": r[4],
                    "evidence": json.loads(r[5]) if r[5] else [],
                    "created_at": r[6],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def generate_summary(self, user_id: str, days: int = 7) -> str:
        """Generate a natural language summary of insights."""
        insights = self.get_insights(user_id, limit=10)
        
        if not insights:
            return "No significant patterns detected in recent memories."
        
        parts = [f"## Dream Synthesis Summary (last {days} days)\n"]
        
        # Group by type
        by_type = defaultdict(list)
        for insight in insights:
            by_type[insight["type"]].append(insight)
        
        for insight_type, items in by_type.items():
            parts.append(f"\n### {insight_type.replace('_', ' ').title()}")
            for item in items[:3]:
                parts.append(f"- **{item['title']}** (confidence: {item['confidence']:.0%})")
                parts.append(f"  {item['content'][:200]}")
        
        return "\n".join(parts)


# Singleton
_synthesizer = None

def get_dream_synthesizer() -> DreamSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = DreamSynthesizer()
    return _synthesizer


if __name__ == "__main__":
    synthesizer = DreamSynthesizer()
    
    print("=== Dream Synthesis Test ===")
    
    # Run synthesis
    result = synthesizer.synthesize(user_id="sen", days=7)
    print(f"Synthesis complete: {result['insights_generated']} insights in {result['duration_seconds']}s")
    
    # Get insights
    insights = synthesizer.get_insights(user_id="sen")
    print(f"\nStored insights: {len(insights)}")
    for i in insights[:5]:
        print(f"  [{i['type']}] {i['title'][:60]} (conf: {i['confidence']:.0%})")
    
    # Generate summary
    summary = synthesizer.generate_summary(user_id="sen")
    print(f"\n{summary[:1000]}")
