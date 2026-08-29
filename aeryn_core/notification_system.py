#!/usr/bin/env python3
"""V41.0 — Phase 1: Notification System.

Features:
- CRUD notifications
- Scheduler (check due notifications)
- Delivery via Telegram/Discord (plugin mode) or webhook
- Quiet hours support
- Notification history
"""

import os, json, sqlite3, asyncio, time, uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlite3 import OperationalError as SQLiteOperationalError

from aeryn_core.config import DATABASE_DIR
DB_PATH = os.path.join(DATABASE_DIR, "notifications.db")


class Notification:
    def __init__(self, user_id: str, title: str, message: str,
                 scheduled_for: str = None, priority: str = "normal",
                 channel: str = "all", metadata: dict = None):
        self.id = None
        self.user_id = user_id
        self.title = title
        self.message = message
        self.scheduled_for = scheduled_for or datetime.now().isoformat()
        self.priority = priority  # low, normal, high, critical
        self.channel = channel  # all, telegram, discord, webhook, dashboard
        self.metadata = metadata or {}
        self.is_sent = False
        self.sent_at = None
        self.created_at = datetime.now().isoformat()


class NotificationManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                scheduled_for TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                channel TEXT DEFAULT 'all',
                metadata TEXT DEFAULT '{}',
                is_sent INTEGER DEFAULT 0,
                sent_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_notif_user_sent ON notifications(user_id, is_sent, scheduled_for);
            CREATE INDEX IF NOT EXISTS idx_notif_due ON notifications(is_sent, scheduled_for);
            
            CREATE TABLE IF NOT EXISTS notification_history (
                id TEXT PRIMARY KEY,
                notification_id TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES notifications(id)
            );
            
            CREATE TABLE IF NOT EXISTS quiet_hours (
                user_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                timezone TEXT DEFAULT 'UTC',
                enabled INTEGER DEFAULT 1
            );
        """)
        conn.commit()
        conn.close()
    
    def create(self, notification: Notification) -> str:
        import uuid
        nid = str(uuid.uuid4())[:12]
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO notifications (id, user_id, title, message, scheduled_for, priority, channel, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nid, notification.user_id, notification.title, notification.message,
            notification.scheduled_for, notification.priority, notification.channel,
            json.dumps(notification.metadata)
        ))
        conn.commit()
        conn.close()
        
        return nid
    
    def get_due(self, user_id: str = None, limit: int = 10) -> List[Dict]:
        """Get due notifications that haven't been sent."""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        if user_id:
            rows = conn.execute("""
                SELECT id, user_id, title, message, scheduled_for, priority, channel, metadata
                FROM notifications
                WHERE user_id = ? AND is_sent = 0 AND scheduled_for <= ?
                ORDER BY scheduled_for
                LIMIT ?
            """, (user_id, now, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, user_id, title, message, scheduled_for, priority, channel, metadata
                FROM notifications
                WHERE is_sent = 0 AND scheduled_for <= ?
                ORDER BY scheduled_for
                LIMIT ?
            """, (now, limit)).fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "user_id": r[1], "title": r[2], "message": r[3],
                "scheduled_for": r[4], "priority": r[5], "channel": r[6],
                "metadata": json.loads(r[7])
            }
            for r in rows
        ]
    
    def mark_sent(self, notification_id: str, status: str = "sent", error: str = None):
        """Mark notification as sent with retry."""
        for attempt in range(3):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    UPDATE notifications SET is_sent = 1, sent_at = ? WHERE id = ?
                """, (datetime.now().isoformat(), notification_id))
                
                conn.execute("""
                    INSERT INTO notification_history (id, notification_id, status, error)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4())[:12], notification_id, status, error))
                conn.commit()
                conn.close()
                return
            except SQLiteOperationalError as e:
                if "database is locked" in str(e) and attempt < 2:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                raise
            except Exception:
                raise
    
    def get_pending(self, user_id: str = None) -> List[Dict]:
        """Get all pending notifications."""
        conn = sqlite3.connect(self.db_path)
        if user_id:
            rows = conn.execute("""
                SELECT id, user_id, title, message, scheduled_for, priority, channel
                FROM notifications WHERE user_id = ? AND is_sent = 0
                ORDER BY scheduled_for
            """, (user_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, user_id, title, message, scheduled_for, priority, channel
                FROM notifications WHERE is_sent = 0
                ORDER BY scheduled_for
            """).fetchall()
        conn.close()
        
        return [
            {"id": r[0], "user_id": r[1], "title": r[2], "message": r[3],
             "scheduled_for": r[4], "priority": r[5], "channel": r[6]}
            for r in rows
        ]
    
    def cancel(self, notification_id: str) -> bool:
        """Cancel a pending notification."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM notifications WHERE id = ? AND is_sent = 0", (notification_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def is_quiet_hours(self, user_id: str) -> bool:
        """Check if currently in quiet hours for user."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT start_time, end_time, enabled FROM quiet_hours WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        
        if not row or not row[2]:
            return False
        
        now = datetime.now().time()
        start = datetime.strptime(row[0], "%H:%M").time()
        end = datetime.strptime(row[1], "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    
    def set_quiet_hours(self, user_id: str, start: str, end: str, timezone: str = "UTC"):
        """Set quiet hours for user (format: HH:MM)."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO quiet_hours (user_id, start_time, end_time, timezone)
            VALUES (?, ?, ?, ?)
        """, (user_id, start, end, timezone))
        conn.commit()
        conn.close()


class NotificationScheduler:
    """Background scheduler that checks and dispatches due notifications."""
    
    def __init__(self, manager: NotificationManager):
        self.manager = manager
        self._running = False
    
    async def start(self):
        """Start the scheduler loop."""
        self._running = True
        while self._running:
            try:
                await self._process_due()
            except Exception as e:
                import traceback
                print(f"Scheduler error: {e}")
                traceback.print_exc()
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _process_due(self):
        """Process due notifications."""
        for attempt in range(3):
            try:
                due = self.manager.get_due(limit=5)
                break
            except Exception as e:
                if "database is locked" in str(e) and attempt < 2:
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    return
        
        for notif in due:
            # Skip if in quiet hours (unless critical)
            if notif["priority"] != "critical" and self.manager.is_quiet_hours(notif["user_id"]):
                continue
            
            # Retry logic for dispatch
            for attempt in range(3):
                try:
                    await self._dispatch(notif)
                    self.manager.mark_sent(notif["id"], "sent")
                    break
                except Exception as e:
                    if "database is locked" in str(e) and attempt < 2:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    self.manager.mark_sent(notif["id"], "failed", str(e))
                    break
    
    async def _dispatch(self, notif: dict):
        """Dispatch notification to appropriate channel."""
        channel = notif["channel"]
        
        if channel in ("all", "dashboard"):
            # Dashboard notification is already in DB, will be fetched by dashboard
            pass
        
        if channel in ("all", "telegram"):
            await self._send_telegram(notif)
        
        if channel in ("all", "discord"):
            await self._send_discord(notif)
        
        if channel in ("all", "webhook"):
            await self._send_webhook(notif)
    
    async def _send_telegram(self, notif: dict):
        """Send via Telegram (placeholder)."""
        # In plugin mode, this would call Hermes Telegram API
        pass
    
    async def _send_discord(self, notif: dict):
        """Send via Discord (placeholder)."""
        # In plugin mode, this would call Hermes Discord API
        pass
    
    async def _send_webhook(self, notif: dict):
        """Send via webhook."""
        webhook_url = notif.get("metadata", {}).get("webhook_url")
        if not webhook_url:
            return
        
        import urllib.request
        body = json.dumps({
            "title": notif["title"],
            "message": notif["message"],
            "priority": notif["priority"],
        }).encode()
        
        req = urllib.request.Request(webhook_url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                pass
        except Exception:
            pass
    
    def stop(self):
        self._running = False


# ── Singleton ─────────────────────────────────

_notification_manager: Optional[NotificationManager] = None
_scheduler: Optional[NotificationScheduler] = None

def get_notification_manager() -> NotificationManager:
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def get_scheduler() -> NotificationScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = NotificationScheduler(get_notification_manager())
    return _scheduler
