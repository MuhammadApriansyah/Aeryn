#!/usr/bin/env python3
"""V40.50 — SLA Monitoring: Uptime tracking, latency, error rates."""

import os, sys, json, sqlite3, time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "sla_monitoring.db")

class SLAMonitor:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sla_metrics (
                id TEXT PRIMARY KEY, service TEXT NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                avg_latency_ms REAL DEFAULT 0.0,
                p95_latency_ms REAL DEFAULT 0.0,
                p99_latency_ms REAL DEFAULT 0.0,
                uptime_percentage REAL DEFAULT 100.0,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sla_alerts (
                id TEXT PRIMARY KEY, service TEXT NOT NULL,
                alert_type TEXT NOT NULL, severity TEXT DEFAULT 'warning',
                message TEXT, is_resolved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved_at TEXT
            );
            CREATE TABLE IF NOT EXISTS latency_log (
                id TEXT PRIMARY KEY, service TEXT NOT NULL,
                latency_ms REAL NOT NULL, endpoint TEXT,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sla_time ON sla_metrics(recorded_at DESC);
            CREATE INDEX IF NOT EXISTS idx_latency_time ON latency_log(recorded_at DESC);
        """)
        conn.commit()
        conn.close()
    
    def record_request(self, service: str, latency_ms: float,
                       success: bool = True, endpoint: str = ""):
        import uuid
        
        conn = sqlite3.connect(self.db_path)
        
        # Log latency
        conn.execute("""
            INSERT INTO latency_log (id, service, latency_ms, endpoint)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], service, latency_ms, endpoint))
        
        # Update metrics (upsert)
        conn.execute("""
            INSERT INTO sla_metrics (id, service, total_requests, successful_requests, failed_requests, avg_latency_ms)
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(service) DO UPDATE SET
                total_requests = total_requests + 1,
                successful_requests = successful_requests + ?,
                failed_requests = failed_requests + ?,
                avg_latency_ms = (avg_latency_ms * total_requests + ?) / (total_requests + 1),
                recorded_at = ?
        """, (service, service, 1 if success else 0, 0 if success else 1, latency_ms,
              1 if success else 0, 0 if success else 1, latency_ms, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_sla_report(self, service: str = None, days: int = 7) -> Dict:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        
        if service:
            row = conn.execute("""
                SELECT service, total_requests, successful_requests, failed_requests,
                       avg_latency_ms, uptime_percentage, recorded_at
                FROM sla_metrics WHERE service = ?
                ORDER BY recorded_at DESC LIMIT 1
            """, (service,)).fetchone()
            
            if not row:
                conn.close()
                return {"error": "Service not found"}
            
            result = {
                "service": row[0],
                "total_requests": row[1],
                "successful_requests": row[2],
                "failed_requests": row[3],
                "avg_latency_ms": row[4],
                "uptime_percentage": row[5],
                "last_updated": row[6],
            }
        else:
            rows = conn.execute("""
                SELECT service, total_requests, successful_requests, failed_requests,
                       avg_latency_ms, uptime_percentage
                FROM sla_metrics ORDER BY service
            """).fetchall()
            
            result = {
                "services": [
                    {"service": r[0], "total_requests": r[1], "successful_requests": r[2],
                     "failed_requests": r[3], "avg_latency_ms": r[4], "uptime_percentage": r[5]}
                    for r in rows
                ]
            }
        
        conn.close()
        return result
    
    def check_sla_breach(self, service: str, max_latency_ms: float = 500,
                         min_uptime_pct: float = 99.0) -> List[Dict]:
        """Check for SLA breaches."""
        breaches = []
        
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT avg_latency_ms, uptime_percentage FROM sla_metrics
            WHERE service = ? ORDER BY recorded_at DESC LIMIT 1
        """, (service,)).fetchone()
        conn.close()
        
        if row:
            if row[0] > max_latency_ms:
                breaches.append({
                    "type": "latency_breach",
                    "severity": "critical",
                    "message": f"Average latency {row[0]:.0f}ms exceeds threshold {max_latency_ms}ms",
                })
            if row[1] < min_uptime_pct:
                breaches.append({
                    "type": "uptime_breach",
                    "severity": "critical",
                    "message": f"Uptime {row[1]:.2f}% below threshold {min_uptime_pct}%",
                })
        
        return breaches

_sla = None
def get_sla_monitor() -> SLAMonitor:
    global _sla
    if _sla is None: _sla = SLAMonitor()
    return _sla
