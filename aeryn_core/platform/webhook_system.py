#!/usr/bin/env python3
"""
V41.0 — Webhook System.
Push notifications ke external endpoints.
"""

import os
import json
import uuid
import asyncio
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime

from aeryn_core.database.neon_db import get_neon
from aeryn_core.utils.logger import info, warn, error


class WebhookSystem:
    """Sistem webhook untuk push notifications."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel webhooks."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                events TEXT DEFAULT '["*"]',
                is_active INTEGER DEFAULT 1,
                secret TEXT,
                last_triggered TEXT,
                fail_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhooks(user_id);
        """)
    
    def register(self, user_id: str, url: str, events: List[str] = None,
                 secret: str = None) -> Dict:
        """Registrasi webhook baru."""
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        
        self.db.insert('webhooks', {
            'id': webhook_id,
            'user_id': user_id,
            'url': url,
            'events': json.dumps(events or ["*"]),
            'secret': secret or uuid.uuid4().hex,
        })
        
        info("Webhook registered", user_id=user_id, url=url)
        return {
            "id": webhook_id,
            "url": url,
            "events": events or ["*"],
            "secret": secret,
        }
    
    def unregister(self, webhook_id: str) -> bool:
        """Hapus webhook."""
        self.db.execute("DELETE FROM webhooks WHERE id = %s", (webhook_id,))
        return True
    
    def list_webhooks(self, user_id: str) -> List[Dict]:
        """List webhook milik user."""
        return self.db.fetchall("""
            SELECT id, url, events, is_active, last_triggered, fail_count, created_at
            FROM webhooks
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
    
    async def trigger(self, event_type: str, payload: Dict):
        """Trigger semua webhook yang sesuai."""
        webhooks = self.db.fetchall("""
            SELECT id, url, events, secret FROM webhooks
            WHERE is_active = 1
        """)
        
        for webhook in webhooks:
            events = json.loads(webhook.get('events', '["*"]'))
            
            if "*" not in events and event_type not in events:
                continue
            
            asyncio.create_task(self._send_webhook(webhook, event_type, payload))
    
    async def _send_webhook(self, webhook: Dict, event_type: str, payload: Dict):
        """Kirim HTTP POST ke webhook URL."""
        try:
            data = json.dumps({
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": payload,
            }).encode()
            
            req = urllib.request.Request(
                webhook['url'],
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-ID": webhook['id'],
                    "X-Event-Type": event_type,
                },
                method="POST",
            )
            
            response = urllib.request.urlopen(req, timeout=10)
            
            # Update last_triggered
            self.db.execute(
                "UPDATE webhooks SET last_triggered = %s WHERE id = %s",
                (datetime.now(), webhook['id'])
            )
            
            info("Webhook sent", webhook_id=webhook['id'], event=event_type)
            
        except urllib.error.URLError as e:
            # Increment fail_count
            self.db.execute(
                "UPDATE webhooks SET fail_count = fail_count + 1 WHERE id = %s",
                (webhook['id'],)
            )
            warn("Webhook failed", webhook_id=webhook['id'], error=str(e))


# Singleton
_webhook_system = None

def get_webhook_system() -> WebhookSystem:
    global _webhook_system
    if _webhook_system is None:
        _webhook_system = WebhookSystem()
    return _webhook_system
