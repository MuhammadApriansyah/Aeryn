"""Advanced Features — planning, reflection, proactive suggestions."""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from aeryn_core.utils.config import DATABASE_DIR
import os
import sqlite3


class Planner:
    """Multi-step planning for complex tasks."""
    
    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "plans.db")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                steps TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()
    
    def make_plan(self, goal: str, steps: List[str]) -> Dict[str, Any]:
        """Create a plan from goal and steps."""
        plan = {
            "goal": goal,
            "steps": steps,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO plans (goal, steps, status) VALUES (?, ?, ?)",
            (goal, json.dumps(steps), "pending")
        )
        conn.commit()
        plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        
        plan["id"] = plan_id
        return plan
    
    def decompose(self, goal: str) -> List[str]:
        """Decompose a complex goal into steps."""
        # Simple keyword-based decomposition
        steps = []
        goal_lower = goal.lower()
        
        if any(kw in goal_lower for kw in ["research", "investigate", "find"]):
            steps.append("Search for information")
            steps.append("Collect sources")
            steps.append("Summarize findings")
        elif any(kw in goal_lower for kw in ["build", "create", "make"]):
            steps.append("Plan the structure")
            steps.append("Implement core functionality")
            steps.append("Test and verify")
        elif any(kw in goal_lower for kw in ["fix", "debug", "repair"]):
            steps.append("Reproduce the issue")
            steps.append("Identify root cause")
            steps.append("Apply fix")
            steps.append("Verify fix")
        elif any(kw in goal_lower for kw in ["deploy", "release", "ship"]):
            steps.append("Prepare release")
            steps.append("Run tests")
            steps.append("Deploy")
            steps.append("Monitor")
        else:
            steps.append("Analyze the task")
            steps.append("Break down into sub-tasks")
            steps.append("Execute each sub-task")
            steps.append("Review results")
        
        return steps
    
    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get a plan by id."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT id, goal, steps, status, created_at FROM plans WHERE id = ?", (plan_id,)).fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "goal": row[1],
            "steps": json.loads(row[2]),
            "status": row[3],
            "created_at": row[4],
        }
    
    def update_status(self, plan_id: int, status: str):
        """Update plan status."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE plans SET status = ? WHERE id = ?", (status, plan_id))
        conn.commit()
        conn.close()


class Reflector:
    """Self-reflection on agent output."""
    
    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "reflections.db")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                outcome TEXT NOT NULL,
                lesson TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()
    
    def reflect(self, goal: str, outcome: str, strategy: str = "") -> Dict[str, Any]:
        """Reflect on a task outcome and derive lessons."""
        reflection = {
            "goal": goal,
            "outcome": outcome,
            "strategy": strategy,
            "lesson": self._derive_lesson(goal, outcome, strategy),
            "created_at": datetime.now().isoformat(),
        }
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO reflections (goal, outcome, lesson) VALUES (?, ?, ?)",
            (goal, outcome, reflection["lesson"])
        )
        conn.commit()
        conn.close()
        
        return reflection
    
    def _derive_lesson(self, goal: str, outcome: str, strategy: str) -> str:
        """Derive a lesson from outcome."""
        outcome_lower = outcome.lower()
        
        if any(kw in outcome_lower for kw in ["success", "completed", "passed", "ok", "done"]):
            return f"Strategy '{strategy}' worked well for goal '{goal}'. Reuse it for similar tasks."
        elif any(kw in outcome_lower for kw in ["fail", "error", "timeout", "crashed"]):
            return f"Strategy '{strategy}' failed for goal '{goal}'. Consider alternative approaches."
        else:
            return f"Mixed result for goal '{goal}'. Review strategy '{strategy}' for improvements."
    
    def recent_strategies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent reflection strategies."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT goal, lesson FROM reflections ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [{"goal": r[0], "lesson": r[1]} for r in rows]


class ProactiveEngine:
    """Proactive suggestions for next actions."""
    
    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "proactive.db")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()
    
    def record_action(self, action: str):
        """Record a user action."""
        conn = sqlite3.connect(self.db_path)
        existing = conn.execute(
            "SELECT id, frequency FROM actions WHERE action = ?", (action,)
        ).fetchone()
        
        if existing:
            conn.execute(
                "UPDATE actions SET frequency = ? WHERE id = ?",
                (existing[1] + 1, existing[0])
            )
        else:
            conn.execute("INSERT INTO actions (action) VALUES (?)", (action,))
        
        conn.commit()
        conn.close()
    
    def suggest(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Suggest frequent actions."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT action, frequency FROM actions ORDER BY frequency DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [{"action": r[0], "frequency": r[1]} for r in rows]


# Global instances
_planner = None
_reflector = None
_proactive = None

def get_planner() -> Planner:
    global _planner
    if _planner is None:
        _planner = Planner()
    return _planner

def get_reflector() -> Reflector:
    global _reflector
    if _reflector is None:
        _reflector = Reflector()
    return _reflector

def get_proactive_engine() -> ProactiveEngine:
    global _proactive
    if _proactive is None:
        _proactive = ProactiveEngine()
    return _proactive