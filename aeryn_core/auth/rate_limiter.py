#!/usr/bin/env python3
"""
V41.0 — Rate Limiting + Circuit Breaker.
Fallback to SQLite if Neon PG is unavailable.
"""

import os
import time
import sqlite3
import threading
from typing import Dict, Optional
from collections import defaultdict

DATABASE_DIR = os.environ.get('DATABASE_DIR', 'Personalisasi/Database')
DB_PATH = os.path.join(DATABASE_DIR, 'rate_limiter.db')

DEFAULT_LIMITS = {
    "free": {"requests_per_minute": 60, "requests_per_hour": 500, "requests_per_day": 2000},
    "user": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 5000},
    "admin": {"requests_per_minute": 200, "requests_per_hour": 5000, "requests_per_day": 50000},
}


class RateLimiter:
    """Rate limiter dengan sliding window — SQLite fallback."""
    
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    requested_at REAL,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_user ON rate_limits(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_time ON rate_limits(requested_at)")
            conn.commit()
            conn.close()
    
    def check(self, user_id: str, endpoint: str = "/", method: str = "GET", ip: str = None, ua: str = None) -> Dict:
        now = time.time()
        
        with self._lock:
            conn = sqlite3.connect(DB_PATH)
            
            one_minute_ago = now - 60
            cursor = conn.execute(
                "SELECT COUNT(*) FROM rate_limits WHERE user_id = ? AND requested_at > ?",
                (user_id, one_minute_ago)
            )
            minute_count = cursor.fetchone()[0]
            
            req_id = f"rl_{user_id}_{int(now * 1000)}"
            conn.execute(
                "INSERT INTO rate_limits (id, user_id, endpoint, method, requested_at, ip_address, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (req_id, user_id, endpoint, method, now, ip, ua)
            )
            
            one_hour_ago = now - 3600
            conn.execute("DELETE FROM rate_limits WHERE requested_at < ?", (one_hour_ago,))
            
            conn.commit()
            conn.close()
        
        limits = DEFAULT_LIMITS.get("user")
        allowed = minute_count < limits["requests_per_minute"]
        
        return {
            "allowed": allowed,
            "remaining": max(0, limits["requests_per_minute"] - minute_count - 1),
            "limit": limits["requests_per_minute"],
            "window": "minute",
        }
    
    def reset(self, user_id: str):
        with self._lock:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM rate_limits WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()


class CircuitBreaker:
    """Circuit breaker pattern."""
    
    def __init__(self, max_failures: int = 3, base_wait: float = 5.0):
        self.max_failures = max_failures
        self.base_wait = base_wait
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.state = "open"
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def is_opened(self) -> bool:
        return self.state == "open"
    
    def should_skip(self) -> bool:
        if self.state == "open":
            if time.time() - self.last_failure_time > self.base_wait:
                self.state = "half-open"
                return False
            return True
        return False


_circuit_breaker = None

def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker


def get_rate_limiter() -> RateLimiter:
    return RateLimiter()
