#!/usr/bin/env python3
"""
V41.0 — Metrics Collector.
Collect system and application metrics.
"""

import os
import time
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_DIR = os.environ.get('DATABASE_DIR', 'Personalisasi/Database')
DB_PATH = os.path.join(DATABASE_DIR, 'metrics.db')

class MetricsCollector:
    """Collect and store metrics."""
    
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                metric_name TEXT,
                metric_value REAL,
                labels TEXT DEFAULT '{}'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_time ON metrics(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)")
        conn.commit()
        conn.close()
    
    def record(self, name: str, value: float, labels: Dict = None):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO metrics (timestamp, metric_name, metric_value, labels) VALUES (?, ?, ?, ?)",
            (time.time(), name, value, json.dumps(labels or {}))
        )
        conn.commit()
        conn.close()
    
    def get_recent(self, name: str, minutes: int = 60) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cutoff = time.time() - (minutes * 60)
        cursor = conn.execute(
            "SELECT timestamp, metric_value, labels FROM metrics WHERE metric_name = ? AND timestamp > ? ORDER BY timestamp",
            (name, cutoff)
        )
        results = [{"timestamp": r[0], "value": r[1], "labels": json.loads(r[2])} for r in cursor.fetchall()]
        conn.close()
        return results
    
    def get_stats(self, name: str, minutes: int = 60) -> Dict:
        data = self.get_recent(name, minutes)
        if not data:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}
        
        values = [d["value"] for d in data]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
    
    def cleanup(self, days: int = 30):
        conn = sqlite3.connect(DB_PATH)
        cutoff = time.time() - (days * 86400)
        conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

collector = MetricsCollector()
