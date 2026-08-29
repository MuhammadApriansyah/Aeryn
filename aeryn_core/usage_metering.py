#!/usr/bin/env python3
"""
V41.0 — Phase 3: Usage Metering.
Tracks usage per user for billing with PostgreSQL backend.
"""

import os
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from aeryn_core.neon_db import get_neon
from aeryn_core.logger import info, warn, error


class UsageMetering:
    """Track usage per user for billing."""
    
    def __init__(self):
        self.db = get_neon()
    
    def track(self, user_id: str, event_type: str, endpoint: str = None,
              tokens_input: int = 0, tokens_output: int = 0, cost: float = 0.0,
              metadata: dict = None):
        """Track a usage event."""
        self.db.insert('usage_events', {
            'id': uuid.uuid4().hex,
            'user_id': user_id,
            'event_type': event_type,
            'endpoint': endpoint or '',
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'cost': cost,
            'metadata': json.dumps(metadata or {}),
        })
    
    def get_summary(self, user_id: str = None, days: int = 30) -> Dict:
        """Get usage summary."""
        since = datetime.now() - timedelta(days=days)
        
        if user_id:
            row = self.db.fetchone("""
                SELECT COUNT(*), SUM(tokens_input), SUM(tokens_output), SUM(cost)
                FROM usage_events
                WHERE user_id = %s AND created_at >= %s
            """, (user_id, since))
        else:
            row = self.db.fetchone("""
                SELECT COUNT(*), SUM(tokens_input), SUM(tokens_output), SUM(cost)
                FROM usage_events
                WHERE created_at >= %s
            """, (since,))
        
        return {
            "period_days": days,
            "total_events": row[0] or 0,
            "total_tokens_input": row[1] or 0,
            "total_tokens_output": row[2] or 0,
            "total_cost": row[3] or 0.0,
        }
    
    def get_events(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get recent usage events."""
        return self.db.fetchall("""
            SELECT event_type, endpoint, tokens_input, tokens_output, cost, metadata, created_at
            FROM usage_events
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))


# ── Singleton ─────────────────────────────────

_metering: Optional[UsageMetering] = None

def get_usage_metering() -> UsageMetering:
    global _metering
    if _metering is None:
        _metering = UsageMetering()
    return _metering
