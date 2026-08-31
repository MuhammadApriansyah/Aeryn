#!/usr/bin/env python3
"""V61.1 — Self-Improvement Engine (Recursive) for Aeryn.

Learns from traces, errors, and outcomes to improve:
1. Tool selection accuracy
2. Division routing confidence
3. Response quality
4. Error recovery strategies

Stores learnings in Personalisasi/Database/self_improvement.db
"""
import os
import json
import time
import sqlite3
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Personalisasi", "Database", "self_improvement.db"
)


class SelfImprovementEngine:
    """Recursive self-improvement based on experience."""

    def __init__(self):
        self._init_db()
        self._learnings: List[Dict] = []
        self._patterns: Dict[str, Any] = {}

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS learnings (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                category TEXT,
                pattern TEXT,
                action TEXT,
                outcome TEXT,
                confidence REAL,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_key TEXT UNIQUE,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_used REAL,
                avg_duration_ms REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS improvements (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                area TEXT,
                before_metric REAL,
                after_metric REAL,
                change_description TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category);
            CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
        """)
        conn.commit()
        conn.close()

    def record_learning(self, category: str, pattern: str, action: str,
                       outcome: str, confidence: float = 0.5, metadata: Dict = None):
        """Record a learning from experience."""
        import uuid
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO learnings (id, timestamp, category, pattern, action, outcome, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4())[:12],
            time.time(),
            category,
            pattern,
            action,
            outcome,
            confidence,
            json.dumps(metadata or {}, ensure_ascii=False)[:1000]
        ))
        conn.commit()
        conn.close()

    def record_outcome(self, pattern_type: str, pattern_key: str,
                      success: bool, duration_ms: int = 0):
        """Record success/failure of a pattern."""
        conn = sqlite3.connect(DB_PATH)
        # Check if pattern exists
        cursor = conn.execute(
            "SELECT success_count, fail_count, avg_duration_ms FROM patterns WHERE pattern_type = ? AND pattern_key = ?",
            (pattern_type, pattern_key)
        )
        row = cursor.fetchone()
        
        if row:
            success_count = row[0] + (1 if success else 0)
            fail_count = row[1] + (0 if success else 1)
            avg_duration = ((row[2] * (success_count + fail_count - 1)) + duration_ms) / (success_count + fail_count)
            conn.execute("""
                UPDATE patterns SET success_count = ?, fail_count = ?, last_used = ?, avg_duration_ms = ?
                WHERE pattern_type = ? AND pattern_key = ?
            """, (success_count, fail_count, time.time(), avg_duration, pattern_type, pattern_key))
        else:
            import uuid
            conn.execute("""
                INSERT INTO patterns (id, pattern_type, pattern_key, success_count, fail_count, last_used, avg_duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:12],
                pattern_type,
                pattern_key,
                1 if success else 0,
                0 if success else 1,
                time.time(),
                duration_ms
            ))
        conn.commit()
        conn.close()

    def get_best_action(self, pattern_type: str, pattern_key: str) -> Optional[Dict]:
        """Get the best known action for a pattern based on past success."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT pattern_key, success_count, fail_count, avg_duration_ms
            FROM patterns WHERE pattern_type = ? AND pattern_key = ?
        """, (pattern_type, pattern_key))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        total = row[1] + row[2]
        success_rate = row[1] / total if total > 0 else 0
        return {
            "pattern_key": row[0],
            "success_count": row[1],
            "fail_count": row[2],
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": row[3],
            "confidence": min(total / 10.0, 1.0),  # More data = higher confidence
        }

    def get_reliable_patterns(self, pattern_type: str, min_success_rate: float = 0.7) -> List[Dict]:
        """Get patterns that are reliably successful."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT pattern_key, success_count, fail_count, avg_duration_ms
            FROM patterns WHERE pattern_type = ? AND (success_count + fail_count) >= 3
        """, (pattern_type,))
        results = []
        for row in cursor.fetchall():
            total = row[1] + row[2]
            rate = row[1] / total if total > 0 else 0
            if rate >= min_success_rate:
                results.append({
                    "pattern_key": row[0],
                    "success_rate": round(rate, 2),
                    "total_uses": total,
                    "avg_duration_ms": row[3],
                })
        conn.close()
        return sorted(results, key=lambda x: x["success_rate"], reverse=True)

    def get_problematic_patterns(self, pattern_type: str, max_success_rate: float = 0.4) -> List[Dict]:
        """Get patterns that frequently fail (need improvement)."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT pattern_key, success_count, fail_count, avg_duration_ms
            FROM patterns WHERE pattern_type = ? AND (success_count + fail_count) >= 2
        """, (pattern_type,))
        results = []
        for row in cursor.fetchall():
            total = row[1] + row[2]
            rate = row[1] / total if total > 0 else 0
            if rate <= max_success_rate:
                results.append({
                    "pattern_key": row[0],
                    "success_rate": round(rate, 2),
                    "total_uses": total,
                    "needs_improvement": True,
                })
        conn.close()
        return results

    def generate_improvement_report(self) -> Dict:
        """Generate a report of what needs improvement."""
        conn = sqlite3.connect(DB_PATH)
        
        # Total stats
        cursor = conn.execute("SELECT COUNT(*), category FROM learnings GROUP BY category")
        categories = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor = conn.execute("SELECT COUNT(*), pattern_type FROM patterns GROUP BY pattern_type")
        pattern_types = {row[1]: row[0] for row in cursor.fetchall()}
        
        cursor = "SELECT COUNT(*) FROM improvements"
        total_improvements = conn.execute(cursor).fetchone()[0]
        
        conn.close()
        
        return {
            "total_learnings": sum(categories.values()),
            "categories": categories,
            "pattern_types": pattern_types,
            "total_improvements": total_improvements,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on data."""
        recs = []
        
        # Check tool patterns
        problematic = self.get_problematic_patterns("tool_selection", 0.4)
        for p in problematic:
            recs.append(f"Tool '{p['pattern_key']}' has low success rate ({p['success_rate']}). Consider retraining or replacing.")
        
        # Check division routing
        routing = self.get_problematic_patterns("division_routing", 0.5)
        for r in routing:
            recs.append(f"Routing to '{r['pattern_key']}' is unreliable. Review intent detection.")
        
        if not recs:
            recs.append("All patterns performing within acceptable parameters.")
        
        return recs

    def adapt(self) -> Dict:
        """Run adaptation cycle — adjust behavior based on learnings."""
        changes = []
        
        # Adapt tool selection thresholds
        reliable_tools = self.get_reliable_patterns("tool_selection", 0.8)
        for tool in reliable_tools:
            changes.append({
                "type": "tool_boost",
                "tool": tool["pattern_key"],
                "action": f"Boost priority for {tool['pattern_key']} (success rate: {tool['success_rate']})"
            })
        
        # Adapt division routing
        reliable_routes = self.get_reliable_patterns("division_routing", 0.8)
        for route in reliable_routes:
            changes.append({
                "type": "route_boost",
                "route": route["pattern_key"],
                "action": f"Route {route['pattern_key']} more aggressively (success rate: {route['success_rate']})"
            })
        
        # Record the adaptation
        if changes:
            conn = sqlite3.connect(DB_PATH)
            import uuid
            conn.execute("""
                INSERT INTO improvements (id, timestamp, area, before_metric, after_metric, change_description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:12],
                time.time(),
                "adaptive_tuning",
                0,
                len(changes),
                json.dumps(changes, ensure_ascii=False)[:1000]
            ))
            conn.commit()
            conn.close()
        
        return {"changes": changes, "timestamp": time.time()}


# Singleton
_engine = None

def get_self_improvement() -> SelfImprovementEngine:
    global _engine
    if _engine is None:
        _engine = SelfImprovementEngine()
    return _engine
