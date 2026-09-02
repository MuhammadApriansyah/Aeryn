"""Memory Write — auto-save facts after conversation."""

import os
import json
import sqlite3
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from aeryn_core.utils.config import DATABASE_DIR, VAULT_DIR


class MemoryWrite:
    """Save important information after conversation."""
    
    def __init__(self):
        self.vault_dir = VAULT_DIR
        self.db_path = os.path.join(DATABASE_DIR, "memories.db")
    
    def extract_facts(self, text: str) -> List[Dict[str, str]]:
        """Extract facts from text."""
        facts = []
        
        # Simple fact extraction: look for "X is Y" patterns
        patterns = [
            r'(\w+)\s+is\s+([^\n\.]+)',
            r'(\w+)\s+are\s+([^\n\.]+)',
            r'(\w+)\s+was\s+([^\n\.]+)',
            r'(\w+)\s+has\s+([^\n\.]+)',
            r'(\w+)\s+can\s+([^\n\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                facts.append({
                    "subject": match[0],
                    "predicate": match[1],
                    "text": f"{match[0]} is {match[1]}",
                })
        
        return facts
    
    def save_fact(self, fact: str, source: str = "conversation", metadata: Dict[str, str] = None):
        """Save a fact to memory."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO memories (content, source, metadata) VALUES (?, ?, ?)",
            (fact, source, json.dumps(metadata or {}))
        )
        conn.commit()
        conn.close()
    
    def save_to_vault(self, filename: str, content: str, layer: str = "Raw"):
        """Save content to vault."""
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir, exist_ok=True)
        
        filepath = os.path.join(self.vault_dir, layer, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def save_conversation_summary(self, session_id: str, messages: List[Dict[str, str]]):
        """Save a summary of the conversation."""
        summary_lines = []
        for msg in messages[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            summary_lines.append(f"{role}: {content}")
        
        summary = "\n".join(summary_lines)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO memories (content, source, metadata) VALUES (?, ?, ?)",
            (summary, "conversation_summary", json.dumps({"session_id": session_id}))
        )
        conn.commit()
        conn.close()
    
    def learn_preference(self, user_id: str, key: str, value: str):
        """Learn user preference."""
        try:
            from aeryn_core.memory.enhanced_memory import EnhancedMemory
            memory = EnhancedMemory()
            memory.learn_preference(user_id, key, value)
        except:
            pass
    
    def save_entity(self, name: str, entity_type: str, metadata: Dict[str, str] = None):
        """Save an entity."""
        try:
            from aeryn_core.memory.entity_resolution import get_entity_resolver
            resolver = get_entity_resolver()
            resolver.register_entity(name, entity_type, metadata)
        except:
            pass


# Global instance
_write = None

def get_memory_write() -> MemoryWrite:
    """Get global memory write instance."""
    global _write
    if _write is None:
        _write = MemoryWrite()
    return _write
