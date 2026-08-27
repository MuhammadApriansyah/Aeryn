#!/usr/bin/env python3
"""V39.66 — Feature: Scheduler + Memory Consolidation.

Scheduler: Check reminders, trigger notifications.
Memory: Daily reflection, fact extraction, consolidation.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI, LAYER_DAILY
from aeryn_core.social_memory import SocialMemory
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.config import DATABASE_DIR, ensure_dirs

class ReminderScheduler:
    """Check and trigger reminders."""
    
    def __init__(self):
        self._reminder_file = os.path.join(DATABASE_DIR, "reminders.jsonl")
    
    def get_pending(self) -> List[dict]:
        """Get all pending reminders that are due."""
        pending = []
        now = datetime.now()
        
        if not os.path.exists(self._reminder_file):
            return pending
        
        try:
            with open(self._reminder_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        reminder = json.loads(line)
                        if reminder.get("status") != "pending":
                            continue
                        due = datetime.fromisoformat(reminder["due"])
                        if due <= now:
                            reminder["_overdue_minutes"] = int((now - due).total_seconds() / 60)
                            pending.append(reminder)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except OSError:
            pass
        
        return pending
    
    def mark_sent(self, reminder_id: str):
        """Mark a reminder as sent."""
        if not os.path.exists(self._reminder_file):
            return
        
        lines = []
        with open(self._reminder_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if r.get("id") == reminder_id:
                        r["status"] = "sent"
                        r["sent_at"] = datetime.now().isoformat()
                    lines.append(json.dumps(r))
                except json.JSONDecodeError:
                    continue
        
        with open(self._reminder_file, "w") as f:
            for line in lines:
                f.write(line + "\n")
    
    def add_reminder(self, text: str, when: str) -> dict:
        """Add a reminder."""
        now = datetime.now()
        try:
            if when.startswith("+"):
                num = int(when[1:-1])
                unit = when[-1]
                if unit == "m":
                    dt = now + timedelta(minutes=num)
                elif unit == "h":
                    dt = now + timedelta(hours=num)
                elif unit == "d":
                    dt = now + timedelta(days=num)
                else:
                    dt = now + timedelta(hours=1)
            else:
                dt = datetime.fromisoformat(when)
        except Exception:
            dt = now + timedelta(hours=1)
        
        reminder = {
            "id": str(uuid.uuid4())[:8],
            "text": text,
            "due": dt.isoformat(),
            "created": now.isoformat(),
            "status": "pending",
        }
        
        os.makedirs(os.path.dirname(self._reminder_file), exist_ok=True)
        with open(self._reminder_file, "a") as f:
            f.write(json.dumps(reminder) + "\n")
        
        return reminder
    
    def get_all(self) -> List[dict]:
        """Get all reminders."""
        reminders = []
        if not os.path.exists(self._reminder_file):
            return reminders
        
        with open(self._reminder_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    reminders.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return reminders


class MemoryConsolidator:
    """Consolidate memories: daily reflection, fact extraction."""
    
    def __init__(self):
        self.vault = AerynVault()
        self.sm = SocialMemory()
        self.search = get_search_engine()
    
    def daily_reflection(self) -> dict:
        """Generate daily reflection."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # Get today's conversations
        conversations = self.vault.search(today, limit=20)
        
        # Build reflection
        reflection_parts = [f"# Daily Reflection — {today}\n"]
        
        # Count interactions
        interaction_count = len(conversations)
        reflection_parts.append(f"Today's interactions: {interaction_count}\n")
        
        # Extract key topics
        topics = set()
        for conv in conversations:
            body = conv.get("preview", "")
            # Simple keyword extraction
            words = body.lower().split()
            for word in words:
                if len(word) > 4:
                    topics.add(word)
        
        if topics:
            reflection_parts.append(f"Topics mentioned: {', '.join(list(topics)[:10])}\n")
        
        reflection_parts.append(f"\nStatus: All systems operational")
        
        reflection = "\n".join(reflection_parts)
        
        # Save to vault
        entry = VaultEntry(
            layer=LAYER_DAILY,
            title=f"Daily Reflection {today}",
            body=reflection,
            tags=["daily", "reflection"],
        )
        self.vault.write(entry)
        
        return {
            "date": today,
            "reflection": reflection,
            "interaction_count": interaction_count,
            "topics": list(topics)[:10],
        }
    
    def extract_facts(self, text: str, user_id: str = "default") -> List[str]:
        """Extract facts from text and store in social memory."""
        extracted = []
        
        # Simple fact extraction (sentence splitting)
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            if len(sentence) > 200:
                continue
            
            # Store as fact
            self.sm.add_fact(user_id, sentence)
            extracted.append(sentence)
        
        return extracted[:5]  # Max 5 facts per call
    
    def search_recent(self, days: int = 7, query: str = "") -> List[dict]:
        """Search recent memories."""
        if query:
            return self.search.search(query, limit=10)
        
        # Search for recent entries
        now = datetime.now()
        results = []
        for i in range(days):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            entries = self.vault.search(date, limit=5)
            results.extend(entries)
        
        return results[:20]


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    ensure_dirs()
    
    scheduler = ReminderScheduler()
    consolidator = MemoryConsolidator()
    
    print("=== Scheduler Test ===")
    r = scheduler.add_reminder("Test reminder +1m", "+1m")
    print(f"Added: {r['id']} due={r['due']}")
    pending = scheduler.get_pending()
    print(f"Pending: {len(pending)}")
    
    print("\n=== Memory Consolidation Test ===")
    result = consolidator.daily_reflection()
    print(f"Reflection: {result['interaction_count']} interactions")
    
    facts = consolidator.extract_facts("Sen suka Python. Sen tinggal di Indonesia. Sen sedang bangun webnovel platform.")
    print(f"Facts extracted: {len(facts)}")
