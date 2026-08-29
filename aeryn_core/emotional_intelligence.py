#!/usr/bin/env python3
"""V40.31 — Emotional Intelligence: Mood tracking and empathy matching."""

import os, sys, json, sqlite3, re
from typing import Dict, List
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "emotional_intelligence.db")

class EmotionalIntelligence:
    MOOD_PATTERNS = {
        "happy": [r"\b(happy|senang|bahagia|gembira|excited|yay|wow|amazing)\b", r"😊|😄|🎉|❤️"],
        "sad": [r"\b(sad|sedih|kecewa|disappointed|frustrated|down|depressed)\b", r"😢|😔|💔"],
        "angry": [r"\b(marah|kesal|annoyed|furious|hate|benci)\b", r"😠|😡"],
        "anxious": [r"\b(anxious|worried|takut|afraid|scared|nervous|stress)\b", r"😰|😨"],
        "neutral": [r"\b(ok|fine|biasa|normal)\b"],
    }
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS mood_history (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, mood TEXT NOT NULL,
                confidence REAL DEFAULT 0.5, context TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS empathy_responses (
                mood TEXT PRIMARY KEY, response_template TEXT NOT NULL, tone TEXT DEFAULT 'neutral'
            );
        """)
        conn.commit()
        conn.close()
        self._seed_responses()
    
    def _seed_responses(self):
        responses = [
            ("happy", "That's wonderful to hear! 🎉", "enthusiastic"),
            ("sad", "I'm sorry to feel that way. I'm here for you. 💙", "supportive"),
            ("angry", "I understand your frustration. Let's work through this together. 🤝", "calming"),
            ("anxious", "Take a deep breath. We'll figure this out step by step. 🌿", "reassuring"),
            ("neutral", "How can I help you today?", "friendly"),
        ]
        conn = sqlite3.connect(self.db_path)
        for r in responses:
            conn.execute("INSERT OR IGNORE INTO empathy_responses (mood, response_template, tone) VALUES (?,?,?)", r)
        conn.commit()
        conn.close()
    
    def detect_mood(self, text: str) -> Dict:
        text_lower = text.lower()
        for mood, patterns in self.MOOD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.I):
                    return {"mood": mood, "confidence": 0.8}
        return {"mood": "neutral", "confidence": 0.5}
    
    def get_empathy_response(self, mood: str) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT response_template FROM empathy_responses WHERE mood=?", (mood,)).fetchone()
        conn.close()
        return row[0] if row else "How can I help?"
    
    def record_mood(self, user_id: str, text: str):
        import uuid
        result = self.detect_mood(text)
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO mood_history (id, user_id, mood, confidence, context) VALUES (?,?,?,?,?)",
                     (str(uuid.uuid4())[:8], user_id, result["mood"], result["confidence"], text[:500]))
        conn.commit()
        conn.close()
        return result

_ei = None
def get_emotional_intelligence() -> EmotionalIntelligence:
    global _ei
    if _ei is None: _ei = EmotionalIntelligence()
    return _ei

if __name__ == "__main__":
    ei = get_emotional_intelligence()
    print(ei.detect_mood("I'm so happy today!"))
    print(ei.get_empathy_response("happy"))
