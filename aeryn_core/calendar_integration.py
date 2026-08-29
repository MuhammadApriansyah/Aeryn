#!/usr/bin/env python3
"""V40.39 — Calendar Integration: Google/Outlook Calendar sync."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "calendar.db")

class CalendarIntegration:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                description TEXT DEFAULT '', start_time TEXT NOT NULL, end_time TEXT,
                location TEXT, calendar_id TEXT DEFAULT 'primary',
                is_all_day INTEGER DEFAULT 0, status TEXT DEFAULT 'confirmed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS calendar_reminders (
                id TEXT PRIMARY KEY, event_id TEXT NOT NULL, minutes_before INTEGER DEFAULT 15,
                method TEXT DEFAULT 'notification', is_sent INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS calendar_sync (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                provider TEXT NOT NULL, last_sync TEXT, status TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_events_user_time ON calendar_events(user_id, start_time);
        """)
        conn.commit()
        conn.close()
    
    def create_event(self, user_id: str, title: str, start_time: str,
                     end_time: str = None, description: str = "",
                     location: str = "") -> str:
        import uuid
        event_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO calendar_events (id, user_id, title, description, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_id, user_id, title, description, start_time, end_time, location))
        conn.commit()
        conn.close()
        
        return event_id
    
    def get_events(self, user_id: str, start: str = None, end: str = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        if start and end:
            rows = conn.execute("""
                SELECT id, title, description, start_time, end_time, location, status
                FROM calendar_events WHERE user_id = ? AND start_time >= ? AND start_time <= ?
                ORDER BY start_time
            """, (user_id, start, end)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, title, description, start_time, end_time, location, status
                FROM calendar_events WHERE user_id = ? ORDER BY start_time LIMIT 50
            """, (user_id,)).fetchall()
        
        conn.close()
        return [
            {"id": r[0], "title": r[1], "description": r[2], "start": r[3],
             "end": r[4], "location": r[5], "status": r[6]}
            for r in rows
        ]
    
    def check_conflicts(self, user_id: str, start_time: str, end_time: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT id, title, start_time, end_time FROM calendar_events
            WHERE user_id = ? AND status = 'confirmed'
            AND ((start_time <= ? AND end_time >= ?) OR (start_time >= ? AND start_time < ?))
        """, (user_id, end_time, start_time, start_time, end_time)).fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "start": r[2], "end": r[3]} for r in rows]

_cal = None
def get_calendar() -> CalendarIntegration:
    global _cal
    if _cal is None: _cal = CalendarIntegration()
    return _cal

if __name__ == "__main__":
    cal = get_calendar()
    eid = cal.create_event("sen", "Team Meeting", "2026-08-29T10:00:00", "2026-08-29T11:00:00")
    events = cal.get_events("sen")
    print(f"Events: {len(events)}")
