#!/usr/bin/env python3
"""
V41.0 — Rate Limiting.
Middleware untuk membatasi request per user.
"""

import time
import uuid
from typing import Dict, Optional
from collections import defaultdict

from aeryn_core.neon_db import get_neon
from aeryn_core.logger import info, warn

# Default limits
DEFAULT_LIMITS = {
    "free": {"requests_per_minute": 60, "requests_per_hour": 500, "requests_per_day": 2000},
    "user": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 5000},
    "admin": {"requests_per_minute": 200, "requests_per_hour": 5000, "requests_per_day": 50000},
}


class RateLimiter:
    """Rate limiter dengan sliding window."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel rate_limits."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_user_time 
            ON rate_limits(user_id, requested_at);
        """)
    
    def _cleanup_old(self, user_id: str):
        """Hapus record lama (> 24 jam)."""
        self.db.execute("""
            DELETE FROM rate_limits 
            WHERE user_id = %s AND requested_at < NOW() - INTERVAL '24 hours';
        """, (user_id,))
    
    def check(self, user_id: str, endpoint: str, method: str = "GET",
              ip_address: str = None, user_agent: str = None,
              role: str = "user") -> Dict:
        """
        Cek apakah request diizinkan.
        Returns: {"allowed": bool, "remaining": int, "reset_at": str}
        """
        limits = DEFAULT_LIMITS.get(role, DEFAULT_LIMITS["user"])
        
        # Cleanup old records
        self._cleanup_old(user_id)
        
        # Count requests in last minute
        minute_ago = time.time() - 60
        hour_ago = time.time() - 3600
        day_ago = time.time() - 86400
        
        # Count per minute
        result = self.db.fetchone("""
            SELECT COUNT(*) as cnt FROM rate_limits
            WHERE user_id = %s AND requested_at > %s
        """, (user_id, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(minute_ago))))
        minute_count = result['cnt'] if result else 0
        
        # Count per hour
        result = self.db.fetchone("""
            SELECT COUNT(*) as cnt FROM rate_limits
            WHERE user_id = %s AND requested_at > %s
        """, (user_id, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(hour_ago))))
        hour_count = result['cnt'] if result else 0
        
        # Count per day
        result = self.db.fetchone("""
            SELECT COUNT(*) as cnt FROM rate_limits
            WHERE user_id = %s AND requested_at > %s
        """, (user_id, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(day_ago))))
        day_count = result['cnt'] if result else 0
        
        # Check limits
        if minute_count >= limits["requests_per_minute"]:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": limits["requests_per_minute"],
                "window": "minute",
                "retry_after": 60 - (time.time() - minute_ago)
            }
        
        if hour_count >= limits["requests_per_hour"]:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": limits["requests_per_hour"],
                "window": "hour",
                "retry_after": 3600 - (time.time() - hour_ago)
            }
        
        if day_count >= limits["requests_per_day"]:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": limits["requests_per_day"],
                "window": "day",
                "retry_after": 86400 - (time.time() - day_ago)
            }
        
        # Record this request
        self.db.insert('rate_limits', {
            'id': uuid.uuid4().hex,
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'ip_address': ip_address or '',
            'user_agent': user_agent or '',
        })
        
        return {
            "allowed": True,
            "remaining": limits["requests_per_minute"] - minute_count - 1,
            "limit": limits["requests_per_minute"],
            "window": "minute"
        }


# Singleton
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
