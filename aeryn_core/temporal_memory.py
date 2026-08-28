#!/usr/bin/env python3
"""V40.8 — Temporal Memory: Time-based queries and historical context.

Features:
- "What did we discuss 3 weeks ago?"
- Time-based queries
- Historical context injection
- Trend detection over time
- Memory timeline
"""

import os
import sys
import json
import re
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/temporal_memory.db")


class TemporalMemory:
    """Time-based memory queries."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memory_timeline (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'conversation',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS time_queries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    parsed_time TEXT,
                    results_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_timeline_user_time ON memory_timeline(user_id, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_timeline_type ON memory_timeline(memory_type, timestamp DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def store(self, user_id: str, memory_type: str, title: str,
              content: str, timestamp: str = None, source: str = "conversation",
              metadata: Dict = None):
        """Store a memory with timestamp."""
        import uuid
        mem_id = str(uuid.uuid4())[:8]
        
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO memory_timeline (id, user_id, timestamp, memory_type, title, content, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mem_id, user_id, timestamp, memory_type, title, content,
                  source, json.dumps(metadata or {})))
            conn.commit()
        finally:
            conn.close()
        
        return mem_id
    
    def query_time(self, user_id: str, query: str) -> Dict:
        """Parse time from query and search."""
        # Parse time expressions
        parsed_time = self._parse_time(query)
        
        if not parsed_time:
            return {"ok": False, "error": "Could not parse time from query"}
        
        # Search memories in time range
        results = self._search_in_range(user_id, parsed_time)
        
        # Log query
        import uuid
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO time_queries (id, user_id, query, parsed_time, results_count)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], user_id, query, parsed_time["iso"], len(results)))
            conn.commit()
        finally:
            conn.close()
        
        return {
            "ok": True,
            "query": query,
            "parsed_time": parsed_time,
            "results": results,
            "count": len(results),
        }
    
    def _parse_time(self, query: str) -> Optional[Dict]:
        """Parse time expressions from natural language."""
        query_lower = query.lower()
        now = datetime.now()
        
        # "X days/weeks/months ago"
        ago_match = re.search(r"(\d+)\s*(day|week|month|year)s?\s*ago", query_lower)
        if ago_match:
            num = int(ago_match.group(1))
            unit = ago_match.group(2)
            
            if unit == "day":
                delta = timedelta(days=num)
            elif unit == "week":
                delta = timedelta(weeks=num)
            elif unit == "month":
                delta = timedelta(days=num * 30)
            elif unit == "year":
                delta = timedelta(days=num * 365)
            else:
                delta = timedelta(days=num)
            
            target = now - delta
            return {
                "type": "ago",
                "value": num,
                "unit": unit,
                "iso": target.isoformat(),
                "display": f"{num} {unit}s ago",
            }
        
        # "yesterday"
        if "yesterday" in query_lower:
            target = now - timedelta(days=1)
            return {
                "type": "yesterday",
                "iso": target.isoformat(),
                "display": "yesterday",
            }
        
        # "last week/month"
        if "last week" in query_lower:
            target = now - timedelta(weeks=1)
            return {
                "type": "last_week",
                "iso": target.isoformat(),
                "display": "last week",
            }
        
        if "last month" in query_lower:
            target = now - timedelta(days=30)
            return {
                "type": "last_month",
                "iso": target.isoformat(),
                "display": "last month",
            }
        
        # "today"
        if "today" in query_lower:
            return {
                "type": "today",
                "iso": now.isoformat(),
                "display": "today",
            }
        
        # "this week"
        if "this week" in query_lower:
            start = now - timedelta(days=now.weekday())
            return {
                "type": "this_week",
                "iso": start.isoformat(),
                "display": "this week",
            }
        
        # Try to parse specific date
        date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", query)
        if date_match:
            try:
                target = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                return {
                    "type": "date",
                    "iso": target.isoformat(),
                    "display": target.strftime("%Y-%m-%d"),
                }
            except Exception:
                pass
        
        return None
    
    def _search_in_range(self, user_id: str, parsed_time: Dict) -> List[Dict]:
        """Search memories in a time range."""
        conn = sqlite3.connect(self.db_path)
        try:
            time_type = parsed_time["type"]
            
            if time_type == "ago":
                # Search around that time (±1 day)
                target = datetime.fromisoformat(parsed_time["iso"])
                start = (target - timedelta(days=1)).isoformat()
                end = (target + timedelta(days=1)).isoformat()
            elif time_type == "yesterday":
                target = datetime.fromisoformat(parsed_time["iso"])
                start = target.replace(hour=0, minute=0, second=0).isoformat()
                end = target.replace(hour=23, minute=59, second=59).isoformat()
            elif time_type == "last_week":
                start = parsed_time["iso"]
                end = datetime.now().isoformat()
            elif time_type == "today":
                start = parsed_time["iso"]
                end = datetime.now().isoformat()
            else:
                start = parsed_time["iso"]
                end = datetime.now().isoformat()
            
            rows = conn.execute("""
                SELECT id, timestamp, memory_type, title, content, source
                FROM memory_timeline
                WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 20
            """, (user_id, start, end)).fetchall()
            
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "type": r[2],
                    "title": r[3],
                    "content": r[4][:500],
                    "source": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def get_timeline(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get memory timeline for a user."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, timestamp, memory_type, title, content, source
                FROM memory_timeline
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (user_id, cutoff)).fetchall()
            
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "type": r[2],
                    "title": r[3],
                    "content": r[4][:300],
                    "source": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def detect_trends(self, user_id: str, days: int = 30) -> List[Dict]:
        """Detect trends in user's memories."""
        memories = self.get_timeline(user_id, days)
        
        if not memories:
            return []
        
        # Count memory types
        type_counts = {}
        for mem in memories:
            mem_type = mem["type"]
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        # Find most common
        trends = []
        for mem_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            trends.append({
                "type": mem_type,
                "count": count,
                "percentage": round(count / len(memories) * 100, 1),
            })
        
        return trends


# Singleton
_temporal = None

def get_temporal_memory() -> TemporalMemory:
    global _temporal
    if _temporal is None:
        _temporal = TemporalMemory()
    return _temporal


if __name__ == "__main__":
    temporal = get_temporal_memory()
    
    print("=== Temporal Memory Test ===")
    
    # Store memories
    temporal.store("sen", "conversation", "Discussed Python", "We talked about Python basics", 
                   timestamp=(datetime.now() - timedelta(days=3)).isoformat())
    temporal.store("sen", "task", "Setup Docker", "Installed Docker on Ubuntu",
                   timestamp=(datetime.now() - timedelta(days=7)).isoformat())
    temporal.store("sen", "conversation", "Discussed AI", "Talked about AI frameworks",
                   timestamp=datetime.now().isoformat())
    
    # Query
    result = temporal.query_time("sen", "What did we discuss 3 days ago?")
    print(f"Query: {result['query']}")
    print(f"Parsed: {result.get('parsed_time', {}).get('display', '?')}")
    print(f"Results: {result.get('count', 0)}")
    
    # Timeline
    timeline = temporal.get_timeline("sen", days=7)
    print(f"Timeline entries: {len(timeline)}")
    
    # Trends
    trends = temporal.detect_trends("sen", days=7)
    print(f"Trends: {trends}")
