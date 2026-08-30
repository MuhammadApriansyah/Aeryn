#!/usr/bin/env python3
"""V40.3 — Self-Improvement Loop: Feedback collection, behavior adjustment, prompt optimization.

Features:
- Feedback collection from user interactions
- Behavior adjustment based on outcomes
- Prompt optimization over time
- Skill crystallization from repeated patterns
- Performance tracking
"""

import os
import sys
import json
import time
import uuid
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(DATABASE_DIR, "self_improvement.db")


class FeedbackCollector:
    """Collect and analyze user feedback."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    interaction_type TEXT NOT NULL,
                    input_text TEXT,
                    output_text TEXT,
                    rating INTEGER,
                    feedback_text TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS behavior_adjustments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    adjustment_type TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    confidence REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS prompt_optimizations (
                    id TEXT PRIMARY KEY,
                    prompt_name TEXT NOT NULL,
                    original_prompt TEXT NOT NULL,
                    optimized_prompt TEXT NOT NULL,
                    improvement_score REAL,
                    applied INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_adjustments_user ON behavior_adjustments(user_id, created_at DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def record_interaction(self, user_id: str, interaction_type: str,
                          input_text: str, output_text: str,
                          session_id: str = None, metadata: Dict = None) -> str:
        """Record an interaction for later feedback."""
        fid = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO feedback (id, user_id, session_id, interaction_type, input_text, output_text, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fid, user_id, session_id, interaction_type, input_text[:1000],
                  output_text[:1000], json.dumps(metadata or {})))
            conn.commit()
        finally:
            conn.close()
        
        return fid
    
    def submit_feedback(self, feedback_id: str, rating: int, feedback_text: str = ""):
        """Submit feedback for an interaction."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE feedback SET rating = ?, feedback_text = ? WHERE id = ?
            """, (rating, feedback_text, feedback_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_feedback_stats(self, user_id: str = None) -> Dict:
        """Get feedback statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            if user_id:
                row = conn.execute("""
                    SELECT COUNT(*), AVG(rating) FROM feedback WHERE user_id = ? AND rating IS NOT NULL
                """, (user_id,)).fetchone()
            else:
                row = conn.execute("""
                    SELECT COUNT(*), AVG(rating) FROM feedback WHERE rating IS NOT NULL
                """).fetchone()
            
            return {
                "total_feedback": row[0] or 0,
                "average_rating": round(row[1] or 0, 2),
            }
        finally:
            conn.close()


class SelfImprovementEngine:
    """Analyze feedback and adjust behavior."""
    
    def __init__(self):
        self.feedback = FeedbackCollector()
    
    def analyze_patterns(self, user_id: str = "default") -> Dict:
        """Analyze feedback patterns for improvement opportunities."""
        conn = sqlite3.connect(self.feedback.db_path)
        try:
            # Get low-rated interactions
            rows = conn.execute("""
                SELECT input_text, output_text, rating, feedback_text
                FROM feedback
                WHERE user_id = ? AND rating IS NOT NULL AND rating < 3
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,)).fetchall()
            
            patterns = []
            for row in rows:
                patterns.append({
                    "input": row[0],
                    "output": row[1],
                    "rating": row[2],
                    "feedback": row[3],
                })
            
            return {
                "low_rated_count": len(patterns),
                "patterns": patterns,
                "suggestions": self._generate_suggestions(patterns),
            }
        finally:
            conn.close()
    
    def _generate_suggestions(self, patterns: List[Dict]) -> List[str]:
        """Generate improvement suggestions from patterns."""
        suggestions = []
        
        if not patterns:
            return ["No improvement suggestions - all feedback is positive!"]
        
        # Analyze common issues
        short_outputs = sum(1 for p in patterns if len(p.get("output", "")) < 50)
        if short_outputs > len(patterns) * 0.5:
            suggestions.append("Consider providing more detailed responses")
        
        # Check for repeated topics
        topics = {}
        for p in patterns:
            words = p.get("input", "").lower().split()
            for word in words:
                if len(word) > 4:
                    topics[word] = topics.get(word, 0) + 1
        
        common_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        if common_topics:
            suggestions.append(f"Common topics in negative feedback: {', '.join(t[0] for t in common_topics)}")
        
        return suggestions
    
    def adjust_behavior(self, user_id: str, adjustment_type: str,
                        old_value: str, new_value: str, reason: str) -> str:
        """Record a behavior adjustment."""
        adj_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.feedback.db_path)
        try:
            conn.execute("""
                INSERT INTO behavior_adjustments (id, user_id, adjustment_type, old_value, new_value, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (adj_id, user_id, adjustment_type, old_value, new_value, reason))
            conn.commit()
        finally:
            conn.close()
        
        return adj_id
    
    def optimize_prompt(self, prompt_name: str, original: str, optimized: str, improvement_score: float = 0.5) -> str:
        """Record a prompt optimization."""
        opt_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.feedback.db_path)
        try:
            conn.execute("""
                INSERT INTO prompt_optimizations (id, prompt_name, original_prompt, optimized_prompt)
                VALUES (?, ?, ?, ?)
            """, (opt_id, prompt_name, original, optimized))
            conn.commit()
        finally:
            conn.close()
        
        return opt_id
    
    def record_metric(self, metric_name: str, value: float, context: str = ""):
        """Record a performance metric."""
        import uuid
        
        conn = sqlite3.connect(self.feedback.db_path)
        try:
            conn.execute("""
                INSERT INTO performance_metrics (id, metric_name, metric_value, context)
                VALUES (?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], metric_name, value, context))
            conn.commit()
        finally:
            conn.close()
    
    def get_improvement_report(self, user_id: str = "default") -> Dict:
        """Generate an improvement report."""
        analysis = self.analyze_patterns(user_id)
        stats = self.feedback.get_feedback_stats(user_id)
        
        conn = sqlite3.connect(self.feedback.db_path)
        try:
            # Get recent adjustments
            rows = conn.execute("""
                SELECT adjustment_type, old_value, new_value, reason
                FROM behavior_adjustments WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 10
            """, (user_id,)).fetchall()
            
            adjustments = [
                {"type": r[0], "old": r[1], "new": r[2], "reason": r[3]}
                for r in rows
            ]
            
            # Get recent optimizations
            rows = conn.execute("""
                SELECT prompt_name, improvement_score
                FROM prompt_optimizations WHERE applied = 1
                ORDER BY created_at DESC LIMIT 10
            """).fetchall()
            
            optimizations = [
                {"prompt": r[0], "score": r[1]} for r in rows
            ]
        finally:
            conn.close()
        
        return {
            "user_id": user_id,
            "feedback_stats": stats,
            "analysis": analysis,
            "recent_adjustments": adjustments,
            "prompt_optimizations": optimizations,
            "generated_at": datetime.now().isoformat(),
        }


# Singleton
_engine = None

def get_self_improvement_engine() -> SelfImprovementEngine:
    global _engine
    if _engine is None:
        _engine = SelfImprovementEngine()
    return _engine


if __name__ == "__main__":
    engine = get_self_improvement_engine()
    
    print("=== Self-Improvement Loop Test ===")
    
    # Record interactions
    fid1 = engine.feedback.record_interaction("sen", "query", "How to install Docker?", "Use apt-get install docker.io")
    fid2 = engine.feedback.record_interaction("sen", "query", "What is Python?", "Python is a programming language")
    
    # Submit feedback
    engine.feedback.submit_feedback(fid1, 5, "Very helpful!")
    engine.feedback.submit_feedback(fid2, 2, "Too brief, need more details")
    
    # Analyze
    analysis = engine.analyze_patterns("sen")
    print(f"Low-rated: {analysis['low_rated_count']}")
    print(f"Suggestions: {analysis['suggestions']}")
    
    # Behavior adjustment
    engine.adjust_behavior("sen", "response_length", "short", "detailed", "User wants more detailed responses")
    
    # Prompt optimization
    engine.optimize_prompt("system_prompt", "You are an AI", "You are Aeryn, a helpful AI assistant", 0.8)
    
    # Record metric
    engine.record_metric("response_time_ms", 150, "docker_query")
    
    # Report
    report = engine.get_improvement_report("sen")
    print(f"Report: {report['feedback_stats']}")
