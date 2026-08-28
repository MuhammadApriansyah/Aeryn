#!/usr/bin/env python3
"""V40.38 — Email Agent: Auto-reply, triage, and email management."""

import os, sys, json, sqlite3, imaplib, smtplib, email
from typing import Dict, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/email_agent.db")

class EmailAgent:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS email_accounts (
                id TEXT PRIMARY KEY, email_address TEXT NOT NULL, provider TEXT,
                imap_server TEXT, smtp_server TEXT, is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_messages (
                id TEXT PRIMARY KEY, account_id TEXT NOT NULL, message_id TEXT,
                sender TEXT, subject TEXT, body TEXT, category TEXT DEFAULT 'inbox',
                is_read INTEGER DEFAULT 0, is_replied INTEGER DEFAULT 0, priority INTEGER DEFAULT 5,
                received_at TEXT, processed_at TEXT, metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS email_rules (
                id TEXT PRIMARY KEY, account_id TEXT, rule_name TEXT,
                condition_field TEXT, condition_value TEXT, action TEXT,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_replies (
                id TEXT PRIMARY KEY, message_id TEXT NOT NULL, reply_text TEXT,
                confidence REAL DEFAULT 0.5, was_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def triage_email(self, sender: str, subject: str, body: str) -> Dict:
        """Categorize and prioritize an email."""
        priority = 5
        category = "inbox"
        
        # Simple rule-based triage
        urgent_keywords = ["urgent", "asap", "important", "deadline", "action required"]
        if any(k in subject.lower() or k in body.lower() for k in urgent_keywords):
            priority = 9
        
        spam_keywords = ["viagra", "free money", "click here", "winner"]
        if any(k in subject.lower() or k in body.lower() for k in spam_keywords):
            category = "spam"
            priority = 1
        
        newsletter_keywords = ["unsubscribe", "newsletter", "digest"]
        if any(k in subject.lower() or k in body.lower() for k in newsletter_keywords):
            category = "newsletter"
            priority = 3
        
        return {
            "priority": priority,
            "category": category,
            "suggested_action": "reply" if priority > 7 else "archive",
        }
    
    def generate_reply(self, sender: str, subject: str, body: str) -> str:
        """Generate a reply using Aeryn."""
        import urllib.request
        prompt = f"Email from {sender}\nSubject: {subject}\n\n{body}\n\nDraft a professional reply:"
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:3010/run",
                data=json.dumps({"goal": prompt}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "")
        except Exception:
            return ""
    
    def store_message(self, account_id: str, message_id: str, sender: str,
                      subject: str, body: str):
        """Store an email message."""
        import uuid
        triage = self.triage_email(sender, subject, body)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO email_messages
            (id, account_id, message_id, sender, subject, body, category, priority, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4())[:8], account_id, message_id, sender, subject, body[:5000],
            triage["category"], triage["priority"], datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        return triage

_email = None
def get_email_agent() -> EmailAgent:
    global _email
    if _email is None: _email = EmailAgent()
    return _email

if __name__ == "__main__":
    agent = get_email_agent()
    triage = agent.triage_email("boss@company.com", "URGENT: Deadline tomorrow", "Please complete the report")
    print(f"Triage: {triage}")
