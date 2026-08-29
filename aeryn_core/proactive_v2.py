#!/usr/bin/env python3
"""V41.0 — Phase 2: Proactive Engine v2 + Daily Briefing.

Enhanced proactive features:
- Daily briefing generation
- Pattern-based suggestions
- Anomaly detection
- Smart follow-ups
- Context-aware nudges
"""

import os, json, sqlite3, asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR


class DailyBriefing:
    """Generate morning/evening briefings."""
    
    def __init__(self):
        self.briefing_db = os.path.join(DATABASE_DIR, "briefings.db")
        os.makedirs(os.path.dirname(self.briefing_db), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.briefing_db)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS briefings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT DEFAULT 'morning',
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_briefing_date ON briefings(user_id, date, type);
        """)
        conn.commit()
        conn.close()
    
    def generate_morning(self, user_id: str) -> Dict:
        """Generate morning briefing."""
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        
        # Gather data
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        pending = db.get_pending_tasks()
        
        # Get yesterday's summary
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Build briefing
        sections = []
        sections.append(f"# 🌅 Good Morning! It's {now.strftime('%A, %B %d')}")
        sections.append("")
        
        # Tasks summary
        if pending:
            sections.append(f"## 📋 Tasks ({len(pending)} pending)")
            for t in pending[:5]:
                status_icon = "⏳" if t.get("status") == "pending" else "🔄"
                sections.append(f"- {status_icon} {t.get('title', 'Untitled')}")
            sections.append("")
        
        # Weather placeholder
        sections.append("## 🌤️ Weather")
        sections.append("- Check local weather for today")
        sections.append("")
        
        # Calendar placeholder
        sections.append("## 📅 Today")
        sections.append("- No upcoming events")
        sections.append("")
        
        # Suggestions
        sections.append("## 💡 Suggestions")
        if pending:
            high_prio = [t for t in pending if t.get("priority", 0) >= 7]
            if high_prio:
                sections.append(f"- You have {len(high_prio)} high-priority tasks. Start with: {high_prio[0].get('title', '')}")
        sections.append("- Take breaks every 90 minutes")
        sections.append("")
        
        content = "\n".join(sections)
        
        # Store
        import uuid
        conn = sqlite3.connect(self.briefing_db)
        conn.execute("""
            INSERT OR REPLACE INTO briefings (id, user_id, date, type, content, metadata)
            VALUES (?, ?, ?, 'morning', ?, ?)
        """, (str(uuid.uuid4())[:12], user_id, today, content, json.dumps({
            "task_count": len(pending),
        })))
        conn.commit()
        conn.close()
        
        return {"date": today, "type": "morning", "content": content}
    
    def generate_evening(self, user_id: str) -> Dict:
        """Generate evening summary."""
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        
        sections = []
        sections.append(f"## 🌙 Evening Summary — {now.strftime('%A, %B %d')}")
        sections.append("")
        sections.append("### Completed Today")
        sections.append("- Review your accomplishments")
        sections.append("")
        sections.append("### Tomorrow")
        sections.append("- Plan your top 3 priorities")
        sections.append("")
        
        content = "\n".join(sections)
        
        import uuid
        conn = sqlite3.connect(self.briefing_db)
        conn.execute("""
            INSERT OR REPLACE INTO briefings (id, user_id, date, type, content, metadata)
            VALUES (?, ?, ?, 'evening', ?, ?)
        """, (str(uuid.uuid4())[:12], user_id, today, content, "{}"))
        conn.commit()
        conn.close()
        
        return {"date": today, "type": "evening", "content": content}
    
    def get_today_briefing(self, user_id: str, briefing_type: str = "morning") -> Optional[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.briefing_db)
        row = conn.execute("""
            SELECT content, metadata, created_at FROM briefings
            WHERE user_id = ? AND date = ? AND type = ?
        """, (user_id, today, briefing_type)).fetchone()
        conn.close()
        
        if row:
            return {"content": row[0], "metadata": json.loads(row[1]), "created_at": row[2]}
        return None


class ProactiveEngineV2:
    """Enhanced proactive engine with pattern detection."""
    
    def __init__(self):
        self.pattern_db = os.path.join(DATABASE_DIR, "patterns.db")
        os.makedirs(os.path.dirname(self.pattern_db), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.pattern_db)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                occurrences INTEGER DEFAULT 1,
                last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pattern_user ON patterns(user_id, pattern_type);
            
            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT DEFAULT 'low',
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def detect_patterns(self, user_id: str) -> List[Dict]:
        """Detect usage patterns."""
        patterns = []
        
        # Check task patterns
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        tasks = db.get_all_tasks()
        
        if len(tasks) > 5:
            # Detect high-priority clustering
            high_prio = [t for t in tasks if t.get("priority", 0) >= 7]
            if len(high_prio) > len(tasks) * 0.5:
                patterns.append({
                    "type": "high_priority_clustering",
                    "description": f"{len(high_prio)}/{len(tasks)} tasks are high priority",
                    "confidence": 0.8,
                })
        
        # Store patterns
        conn = sqlite3.connect(self.pattern_db)
        for p in patterns:
            import uuid
            conn.execute("""
                INSERT OR REPLACE INTO patterns (id, user_id, pattern_type, description, confidence, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:12], user_id, p["type"], p["description"], p["confidence"], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return patterns
    
    def detect_anomalies(self, user_id: str) -> List[Dict]:
        """Detect anomalies in usage."""
        anomalies = []
        
        # Check for stale tasks
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        tasks = db.get_all_tasks()
        
        stale = [t for t in tasks if t.get("status") == "pending"]
        if len(stale) > 10:
            anomalies.append({
                "type": "task_overflow",
                "description": f"You have {len(stale)} pending tasks. Consider reviewing or delegating.",
                "severity": "medium",
            })
        
        # Store anomalies
        conn = sqlite3.connect(self.pattern_db)
        for a in anomalies:
            import uuid
            conn.execute("""
                INSERT INTO anomalies (id, user_id, anomaly_type, description, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:12], user_id, a["type"], a["description"], a["severity"]))
        conn.commit()
        conn.close()
        
        return anomalies
    
    def generate_smart_followups(self, user_id: str) -> List[Dict]:
        """Generate smart follow-up suggestions."""
        followups = []
        
        # Check for incomplete tasks
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        tasks = db.get_all_tasks()
        
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]
        for t in in_progress:
            followups.append({
                "type": "follow_up",
                "title": f"Follow up: {t.get('title', 'Task')}",
                "description": f"This task has been in progress. Need help?",
                "priority": "normal",
                "metadata": {"task_id": t.get("id")},
            })
        
        return followups


# ── Singletons ────────────────────────────────

_briefing: Optional[DailyBriefing] = None
_proactive_v2: Optional[ProactiveEngineV2] = None

def get_daily_briefing() -> DailyBriefing:
    global _briefing
    if _briefing is None:
        _briefing = DailyBriefing()
    return _briefing

def get_proactive_v2() -> ProactiveEngineV2:
    global _proactive_v2
    if _proactive_v2 is None:
        _proactive_v2 = ProactiveEngineV2()
    return _proactive_v2
