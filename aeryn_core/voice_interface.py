#!/usr/bin/env python3
"""V40.33 — Voice Interface: Speech-to-text and text-to-speech capabilities."""

import os, sys, json, sqlite3, subprocess
from typing import Dict, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/voice.db")

class VoiceInterface:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS voice_commands (
                id TEXT PRIMARY KEY, user_id TEXT, transcript TEXT,
                action TEXT, success INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio to text using Whisper or fallback."""
        try:
            result = subprocess.run(
                ["whisper", audio_path, "--model", "tiny", "--output_format", "txt", "--output_dir", "/tmp"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                # Read output file
                out_path = audio_path.rsplit(".", 1)[0] + ".txt"
                if os.path.exists(out_path):
                    with open(out_path) as f:
                        return f.read().strip()
        except Exception:
            pass
        return ""
    
    def speak(self, text: str, output_path: str = "/tmp/aeryn_speech.wav") -> str:
        """Convert text to speech using espeak or similar."""
        try:
            subprocess.run(
                ["espeak", "-w", output_path, text],
                capture_output=True, timeout=30
            )
            return output_path
        except Exception:
            return ""
    
    def process_voice_command(self, audio_path: str, user_id: str = "default") -> Dict:
        """Process a voice command end-to-end."""
        transcript = self.transcribe(audio_path)
        if not transcript:
            return {"ok": False, "error": "Transcription failed"}
        
        import uuid
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO voice_commands (id, user_id, transcript, action)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], user_id, transcript, "voice_input"))
        conn.commit()
        conn.close()
        
        return {"ok": True, "transcript": transcript}

_voice = None
def get_voice() -> VoiceInterface:
    global _voice
    if _voice is None: _voice = VoiceInterface()
    return _voice
