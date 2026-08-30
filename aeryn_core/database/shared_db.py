#!/usr/bin/env python3
"""
V2.0 — Shared DB with PostgreSQL support.

Uses db_adapter to route to PostgreSQL when available, with SQLite fallback.
Maintains the same API as V39.70.
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import threading
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from aeryn_core.utils.config import DATABASE_DIR

# Import PostgreSQL adapter
from aeryn_core.database.db_adapter import get_db, db_execute, db_fetchone, db_fetchall

DB_PATH = os.path.join(DATABASE_DIR, "shared.db")


class SharedDB:
    """Shared database for n8n + Aeryn with PG support."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize all tables."""
        # Ensure PG tables exist (if using PostgreSQL)
        from aeryn_core.database.db_adapter import ensure_pg_tables
        ensure_pg_tables()
        
        # For SQLite, create tables if not exists
        conn = get_db(self.db_path)
        try:
            # Try executescript (SQLite only)
            if hasattr(conn, 'executescript'):
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
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
        finally:
            conn.close()
    
    def _get_conn(self):
        """Get a database connection via adapter."""
        return get_db(self.db_path)
    
    # ── Workflow Runs ─────────────────────────────────────────────
    
    def start_workflow(self, workflow_name: str, trigger_type: str = "manual",
                        input_data: dict = None) -> str:
        """Start tracking a workflow run."""
        run_id = str(uuid.uuid4())[:12]
        with self._lock:
            conn = self._get_conn()
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
            conn = self._get_conn()
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
        conn = self._get_conn()
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
        rid = str(uuid.uuid4())[:8]
        with self._lock:
            conn = self._get_conn()
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
        conn = self._get_conn()
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
            conn = self._get_conn()
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
        conn = self._get_conn()
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
        task_id = str(uuid.uuid4())[:8]
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO task_queue (id, title, description, priority, parent_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (task_id, title, description, priority, parent_id))
                conn.commit()
                return task_id
            finally:
                conn.close()
    
    def get_tasks(self, status: str = None, limit: int = 50) -> List[dict]:
        """Get tasks, optionally filtered by status."""
        conn = self._get_conn()
        try:
            if status:
                rows = conn.execute("""
                    SELECT id, title, description, status, priority, progress, created_at
                    FROM task_queue WHERE status = ?
                    ORDER BY priority DESC, created_at
                    LIMIT ?
                """, (status, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, title, description, status, priority, progress, created_at
                    FROM task_queue
                    ORDER BY priority DESC, created_at
                    LIMIT ?
                """, (limit,)).fetchall()
            
            return [
                {
                    "id": r[0], "title": r[1], "description": r[2],
                    "status": r[3], "priority": r[4], "progress": r[5],
                    "created_at": r[6]
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def update_task_progress(self, task_id: str, progress: float, result: str = None):
        """Update task progress."""
        with self._lock:
            conn = self._get_conn()
            try:
                if progress >= 1.0:
                    conn.execute("""
                        UPDATE task_queue SET progress = 1.0, status = 'completed', 
                        result = ?, completed_at = ?, updated_at = ?
                        WHERE id = ?
                    """, (result, datetime.now().isoformat(), datetime.now().isoformat(), task_id))
                else:
                    conn.execute("""
                        UPDATE task_queue SET progress = ?, result = ?, updated_at = ?
                        WHERE id = ?
                    """, (progress, result, datetime.now().isoformat(), task_id))
                conn.commit()
            finally:
                conn.close()
    
    def complete_task(self, task_id: str, result: str = None):
        """Mark task as completed."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    UPDATE task_queue SET status = 'completed', progress = 1.0, 
                    result = ?, completed_at = ?, updated_at = ?
                    WHERE id = ?
                """, (result, datetime.now().isoformat(), datetime.now().isoformat(), task_id))
                conn.commit()
            finally:
                conn.close()
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    UPDATE task_queue SET status = 'failed', error = ?, updated_at = ?
                    WHERE id = ?
                """, (error, datetime.now().isoformat(), task_id))
                conn.commit()
            finally:
                conn.close()
    
    # ── Notifications ─────────────────────────────────────────────
    
    def add_notification(self, message: str, channel: str = "log",
                        target: str = "all", level: str = "info") -> str:
        """Add a notification."""
        nid = str(uuid.uuid4())[:8]
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO notifications (id, channel, target, message, level)
                    VALUES (?, ?, ?, ?, ?)
                """, (nid, channel, target, message, level))
                conn.commit()
                return nid
            finally:
                conn.close()
    
    def get_pending_notifications(self, limit: int = 50) -> List[dict]:
        """Get pending notifications."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT id, channel, target, message, level, created_at
                FROM notifications WHERE status = 'pending'
                ORDER BY created_at
                LIMIT ?
            """, (limit,)).fetchall()
            return [
                {"id": r[0], "channel": r[1], "target": r[2],
                 "message": r[3], "level": r[4], "created_at": r[5]}
                for r in rows
            ]
        finally:
            conn.close()
    
    def mark_notification_sent(self, notification_id: str, error: str = None):
        """Mark notification as sent."""
        with self._lock:
            conn = self._get_conn()
            try:
                status = 'sent' if not error else 'failed'
                conn.execute("""
                    UPDATE notifications SET status = ?, sent_at = ?, error = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), error, notification_id))
                conn.commit()
            finally:
                conn.close()
    
    # ── Daily Log ─────────────────────────────────────────────────
    
    def add_daily_log(self, date: str, reflection: str = "",
                     interactions: int = 0, reminders_sent: int = 0,
                     tasks_completed: int = 0, system_health: str = "unknown",
                     notes: dict = None) -> str:
        """Add or update daily log entry."""
        log_id = str(uuid.uuid4())[:8]
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO daily_log (id, date, reflection, interactions, 
                    reminders_sent, tasks_completed, system_health, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        reflection = EXCLUDED.reflection,
                        interactions = EXCLUDED.interactions,
                        reminders_sent = EXCLUDED.reminders_sent,
                        tasks_completed = EXCLUDED.tasks_completed,
                        system_health = EXCLUDED.system_health,
                        notes = EXCLUDED.notes
                """, (log_id, date, reflection, interactions, reminders_sent,
                      tasks_completed, system_health, json.dumps(notes or {})))
                conn.commit()
                return log_id
            except Exception:
                # SQLite doesn't support ON CONFLICT DO UPDATE before 3.24
                # Fallback for SQLite
                try:
                    conn.rollback()
                    conn.execute("""
                        INSERT OR REPLACE INTO daily_log (id, date, reflection, interactions,
                        reminders_sent, tasks_completed, system_health, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (log_id, date, reflection, interactions, reminders_sent,
                          tasks_completed, system_health, json.dumps(notes or {})))
                    conn.commit()
                    return log_id
                except Exception:
                    conn.rollback()
                    raise
            finally:
                conn.close()
    
    def get_daily_logs(self, limit: int = 30) -> List[dict]:
        """Get recent daily logs."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT id, date, reflection, interactions, reminders_sent,
                       tasks_completed, system_health, notes, created_at
                FROM daily_log ORDER BY date DESC LIMIT ?
            """, (limit,)).fetchall()
            
            return [
                {
                    "id": r[0], "date": r[1], "reflection": r[2],
                    "interactions": r[3], "reminders_sent": r[4],
                    "tasks_completed": r[5], "system_health": r[6],
                    "notes": json.loads(r[7]) if r[7] else {},
                    "created_at": r[8]
                }
                for r in rows
            ]
        finally:
            conn.close()


# ── Singleton ─────────────────────────────────────────────────────

_shared_db = None

def get_shared_db() -> SharedDB:
    global _shared_db
    if _shared_db is None:
        _shared_db = SharedDB()
    return _shared_db


if __name__ == "__main__":
    db = get_shared_db()
    print("Shared DB initialized")
    print("Workflow stats:", db.get_workflow_stats())