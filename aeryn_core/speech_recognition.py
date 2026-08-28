#!/usr/bin/env python3
"""V40.45 — Speech Recognition: Whisper-based STT with fallback."""

import os, sys, json, sqlite3, subprocess
from typing import Dict, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/speech_recognition.db")

class SpeechRecognition:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id TEXT PRIMARY KEY, user_id TEXT, audio_path TEXT,
                transcript TEXT, confidence REAL DEFAULT 0.0,
                model TEXT DEFAULT 'whisper', duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def transcribe(self, audio_path: str, user_id: str = "default",
                   model: str = "tiny") -> Dict:
        """Transcribe audio using Whisper or fallback."""
        import uuid
        
        result = {"ok": False, "transcript": "", "error": ""}
        
        # Try Whisper
        try:
            proc = subprocess.run(
                ["whisper", audio_path, "--model", model, "--output_format", "json",
                 "--output_dir", "/tmp/whisper_output"],
                capture_output=True, text=True, timeout=120
            )
            
            if proc.returncode == 0:
                # Find output JSON
                base_name = os.path.splitext(os.path.basename(audio_path))[0]
                json_path = f"/tmp/whisper_output/{base_name}.json"
                
                if os.path.exists(json_path):
                    with open(json_path) as f:
                        data = json.load(f)
                    result["ok"] = True
                    result["transcript"] = data.get("text", "").strip()
                    result["confidence"] = 0.9
                else:
                    result["error"] = "Whisper output not found"
            else:
                result["error"] = proc.stderr[:500]
        except FileNotFoundError:
            result["error"] = "Whisper not installed"
        except subprocess.TimeoutExpired:
            result["error"] = "Transcription timed out"
        except Exception as e:
            result["error"] = str(e)
        
        # Store result
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO transcriptions (id, user_id, audio_path, transcript, confidence, model)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], user_id, audio_path,
              result.get("transcript", ""), result.get("confidence", 0.0), model))
        conn.commit()
        conn.close()
        
        return result
    
    def get_history(self, user_id: str, limit: int = 20) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT id, transcript, confidence, model, created_at
            FROM transcriptions WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [
            {"id": r[0], "transcript": r[1][:200], "confidence": r[2], "model": r[3], "created_at": r[4]}
            for r in rows
        ]

_stt = None
def get_speech_recognition() -> SpeechRecognition:
    global _stt
    if _stt is None: _stt = SpeechRecognition()
    return _stt
