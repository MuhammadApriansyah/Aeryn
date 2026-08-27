#!/usr/bin/env python3
"""V39.70 — Shared SQLite Database for n8n + Aeryn.

Schema:
- workflow_runs: track n8n executions
- reminders: scheduled reminders
- task_queue: long-horizon tasks
- notifications: outbound notifications
- daily_log: daily reflection entries
"""

import os
import sys
import json
import time
import sqlite3
import threading
from typing import Optional, List, Dict
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/shared.db")


class SharedDB:
    """Shared database for n8n + Aeryn."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize all tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                -- Workflow execution tracking
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    workflow_name TEXT NOT NULL,
                    trigger_type TEXT DEFAULT 'manual',
                    status TEXT DEFAULT 'running',
                    started_at REAL,
                    completed_at REAL,
                    input_data TEXT DEFAULT '{}',
                    output_data TEXT DEFAULT '{}',
                    error TEXT,
                    duration_ms INTEGER DEFAULT 0
                );
                
                -- Reminders
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    source TEXT DEFAULT 'aeryn',
                    target TEXT DEFAULT 'all',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    sent_at TEXT,
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Task queue (long-horizon)
                CREATE TABLE IF NOT EXISTS task_queue (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    progress REAL DEFAULT 0.0,
                    result TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                );
                
                -- Notifications
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    channel TEXT DEFAULT 'log',
                    target TEXT DEFAULT 'all',
                    message TEXT NOT NULL,
                    level TEXT DEFAULT 'info',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    sent_at TEXT,
                    error TEXT
                );
                
                -- Daily log (reflections, summaries)
                CREATE TABLE IF NOT EXISTS daily_log (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL UNIQUE,
                    reflection TEXT DEFAULT '',
                    interactions INTEGER DEFAULT 0,
                    reminders_sent INTEGER DEFAULT 0,
                    tasks_completed INTEGER DEFAULT 0,
                    system_health TEXT DEFAULT 'unknown',
                    notes TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Indexes
                CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status, due_at);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON task_queue(status, priority DESC);
                CREATE INDEX IF NOT EXISTS idx_notifications ON notifications(status, channel);
                CREATE INDEX IF NOT EXISTS idx_workflow_runs ON workflow_runs(status, workflow_name);
            """)
            conn.commit()
        finally:
            conn.close()
    
    # ── Workflow Runs ─────────────────────────────────────────────
    
    def start_workflow(self, workflow_name: str, trigger_type: str = "manual",
                        input_data: dict = None) -> str:
        """Start tracking a workflow run."""
        import uuid
        run_id = str(uuid.uuid4())[:12]
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO workflow_runs (id, workflow_name, trigger_type, status, started_at, input_data)
                    VALUES (?, ?, ?, 'running', ?, ?)
                """, (run_id, workflow_name, trigger_type, time.time(),
                      json.dumps(input_data or {})))
                conn.commit()
                return run_id
            finally:
                conn.close()
    
    def complete_workflow(self, run_id: str, output_data: dict = None, error: str = None):
        """Complete a workflow run."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                status = 'completed' if not error else 'failed'
                row = conn.execute(
                    "SELECT started_at FROM workflow_runs WHERE id = ?", (run_id,)
                ).fetchone()
                duration = int((time.time() - row[0]) * 1000) if row else 0
                
                conn.execute("""
                    UPDATE workflow_runs 
                    SET status = ?, completed_at = ?, output_data = ?, error = ?, duration_ms = ?
                    WHERE id = ?
                """, (status, time.time(), json.dumps(output_data or {}), error, duration, run_id))
                conn.commit()
            finally:
                conn.close()
    
    def get_workflow_stats(self) -> dict:
        """Get workflow execution statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            total = conn.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0]
            success = conn.execute("SELECT COUNT(*) FROM workflow_runs WHERE status='completed'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM workflow_runs WHERE status='failed'").fetchone()[0]
            running = conn.execute("SELECT COUNT(*) FROM workflow_runs WHERE status='running'").fetchone()[0]
            avg_duration = conn.execute(
                "SELECT AVG(duration_ms) FROM workflow_runs WHERE completed_at IS NOT NULL"
            ).fetchone()[0]
            
            return {
                "total_runs": total,
                "successful": success,
                "failed": failed,
                "running": running,
                "avg_duration_ms": round(avg_duration or 0, 1),
            }
        finally:
            conn.close()
    
    # ── Reminders ─────────────────────────────────────────────────
    
    def add_reminder(self, text: str, due_at: str, source: str = "aeryn",
                     target: str = "all", metadata: dict = None) -> str:
        """Add a reminder."""
        import uuid
        rid = str(uuid.uuid4())[:8]
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO reminders (id, text, due_at, source, target, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (rid, text, due_at, source, target, json.dumps(metadata or {})))
                conn.commit()
                return rid
            finally:
                conn.close()
    
    def get_due_reminders(self) -> List[dict]:
        """Get all pending reminders that are due."""
        conn = sqlite3.connect(self.db_path)
        try:
            now = datetime.now().isoformat()
            rows = conn.execute("""
                SELECT id, text, due_at, source, target, metadata FROM reminders
                WHERE status = 'pending' AND due_at <= ?
                ORDER BY due_at
            """, (now,)).fetchall()
            
            return [
                {
                    "id": r[0], "text": r[1], "due_at": r[2],
                    "source": r[3], "target": r[4],
                    "metadata": json.loads(r[5]) if r[5] else {}
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def mark_reminder_sent(self, reminder_id: str):
        """Mark reminder as sent."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE reminders SET status = 'sent', sent_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), reminder_id))
                conn.commit()
            finally:
                conn.close()
    
    def get_all_reminders(self) -> List[dict]:
        """Get all reminders."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, text, due_at, status, source FROM reminders
                ORDER BY due_at DESC LIMIT 50
            """).fetchall()
            return [{"id": r[0], "text": r[1], "due_at": r[2], "status": r[3], "source": r[4]} for r in rows]
        finally:
            conn.close()
    
    # ── Tasks ─────────────────────────────────────────────────────
    
    def add_task(self, title: str, description: str = "", priority: int = 5,
                 parent_id: str = None) -> str:
        """Add a task to the queue."""
        import uuid
        tid = str(uuid.uuid4())[:8]
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO task_queue (id, parent_id, title, description, priority)
                    VALUES (?, ?, ?, ?, ?)
                """, (tid, parent_id, title, description, priority))
                conn.commit()
                return tid
            finally:
                conn.close()
    
    def get_pending_tasks(self) -> List[dict]:
        """Get pending tasks ordered by priority."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, title, description, priority, progress FROM task_queue
                WHERE status = 'pending' ORDER BY priority DESC, created_at
            """).fetchall()
            return [
                {"id": r[0], "title": r[1], "description": r[2], "priority": r[3], "progress": r[4]}
                for r in rows
            ]
        finally:
            conn.close()
    
    def update_task(self, task_id: str, status: str = None, progress: float = None,
                    result: str = None, error: str = None):
        """Update task status."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                updates = []
                params = []
                if status:
                    updates.append("status = ?")
                    params.append(status)
                    if status == "completed":
                        updates.append("completed_at = ?")
                        params.append(datetime.now().isoformat())
                if progress is not None:
                    updates.append("progress = ?")
                    params.append(progress)
                if result:
                    updates.append("result = ?")
                    params.append(result)
                if error:
                    updates.append("error = ?")
                    params.append(error)
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(task_id)
                
                conn.execute(f"""
                    UPDATE task_queue SET {', '.join(updates)} WHERE id = ?
                """, params)
                conn.commit()
            finally:
                conn.close()
    
    # ── Notifications ─────────────────────────────────────────────
    
    def add_notification(self, message: str, channel: str = "log",
                         target: str = "all", level: str = "info") -> str:
        """Add a notification."""
        import uuid
        nid = str(uuid.uuid4())[:8]
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO notifications (id, channel, target, message, level)
                    VALUES (?, ?, ?, ?, ?)
                """, (nid, channel, target, message, level))
                conn.commit()
                return nid
            finally:
                conn.close()
    
    def get_pending_notifications(self, channel: str = "log") -> List[dict]:
        """Get pending notifications for a channel."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, message, level, target FROM notifications
                WHERE status = 'pending' AND channel = ?
                ORDER BY created_at
            """, (channel,)).fetchall()
            return [{"id": r[0], "message": r[1], "level": r[2], "target": r[3]} for r in rows]
        finally:
            conn.close()
    
    def mark_notification_sent(self, nid: str, error: str = None):
        """Mark notification as sent."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                status = 'failed' if error else 'sent'
                conn.execute("""
                    UPDATE notifications SET status = ?, sent_at = ?, error = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), error, nid))
                conn.commit()
            finally:
                conn.close()
    
    # ── Daily Log ─────────────────────────────────────────────────
    
    def get_or_create_daily_log(self, date: str = None) -> dict:
        """Get or create daily log entry."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT date, reflection, interactions, reminders_sent, tasks_completed, system_health, notes FROM daily_log WHERE date = ?",
                (date,)
            ).fetchone()
            
            if row:
                return {
                    "date": row[0], "reflection": row[1], "interactions": row[2],
                    "reminders_sent": row[3], "tasks_completed": row[4],
                    "system_health": row[5], "notes": json.loads(row[6]) if row[6] else {}
                }
            else:
                conn.execute("""
                    INSERT INTO daily_log (date) VALUES (?)
                """, (date,))
                conn.commit()
                return {"date": date, "reflection": "", "interactions": 0, "reminders_sent": 0, "tasks_completed": 0, "system_health": "unknown", "notes": {}}
        finally:
            conn.close()
    
    def update_daily_log(self, date: str = None, **kwargs):
        """Update daily log fields."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                updates = []
                params = []
                for key, value in kwargs.items():
                    if key == "notes" and isinstance(value, dict):
                        updates.append(f"{key} = ?")
                        params.append(json.dumps(value))
                    else:
                        updates.append(f"{key} = ?")
                        params.append(value)
                params.append(date)
                
                conn.execute(f"""
                    UPDATE daily_log SET {', '.join(updates)} WHERE date = ?
                """, params)
                conn.commit()
            finally:
                conn.close()
    
    def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Get a task by ID."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, parent_id, title, description, status, priority, progress, result, error, created_at, updated_at, completed_at
                FROM task_queue WHERE id = ?
            """, (task_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0], "parent_id": row[1], "title": row[2],
                "description": row[3], "status": row[4], "priority": row[5],
                "progress": row[6], "result": row[7], "error": row[8],
                "created_at": row[9], "updated_at": row[10], "completed_at": row[11]
            }
        finally:
            conn.close()
    
    def get_all_task_ids(self) -> List[dict]:
        """Get all tasks."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, parent_id, title, description, status, priority, progress
                FROM task_queue ORDER BY created_at DESC LIMIT 100
            """).fetchall()
            return [
                {"id": r[0], "parent_id": r[1], "title": r[2], "description": r[3],
                 "status": r[4], "priority": r[5], "progress": r[6]}
                for r in rows
            ]
        finally:
            conn.close()
    
    def get_stats(self) -> dict:
        """Get overall statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            reminders_total = conn.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]
            reminders_pending = conn.execute("SELECT COUNT(*) FROM reminders WHERE status='pending'").fetchone()[0]
            tasks_total = conn.execute("SELECT COUNT(*) FROM task_queue").fetchone()[0]
            tasks_pending = conn.execute("SELECT COUNT(*) FROM task_queue WHERE status='pending'").fetchone()[0]
            tasks_completed = conn.execute("SELECT COUNT(*) FROM task_queue WHERE status='completed'").fetchone()[0]
            notifications_total = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
            workflow_stats = self.get_workflow_stats()
            
            return {
                "reminders": {"total": reminders_total, "pending": reminders_pending},
                "tasks": {"total": tasks_total, "pending": tasks_pending, "completed": tasks_completed},
                "notifications": {"total": notifications_total},
                "workflows": workflow_stats,
            }
        finally:
            conn.close()


# Singleton
_db = None

def get_shared_db() -> SharedDB:
    global _db
    if _db is None:
        _db = SharedDB()
    return _db


if __name__ == "__main__":
    db = SharedDB()
    print("=== Shared Database Test ===")
    
    # Test workflow tracking
    run_id = db.start_workflow("test_workflow", "manual", {"goal": "test"})
    print(f"Workflow started: {run_id}")
    db.complete_workflow(run_id, {"result": "success"})
    print(f"Workflow completed")
    
    # Test reminders
    rid = db.add_reminder("Test reminder due now", datetime.now().isoformat())
    print(f"Reminder added: {rid}")
    due = db.get_due_reminders()
    print(f"Due reminders: {len(due)}")
    
    # Test tasks
    tid = db.add_task("Test task", "Description", priority=8)
    print(f"Task added: {tid}")
    db.update_task(tid, status="in_progress", progress=0.5)
    print(f"Task updated")
    
    # Test notifications
    nid = db.add_notification("Test notification", "log", "all", "info")
    print(f"Notification added: {nid}")
    
    # Test daily log
    log = db.get_or_create_daily_log()
    print(f"Daily log: {log['date']}")
    db.update_daily_log(interactions=5, system_health="healthy")
    
    # Stats
    stats = db.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")
