#!/usr/bin/env python3
"""V40.54 — Image Generation: DALL-E/Midjourney-style generation."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/image_generation.db")

class ImageGenerator:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS generated_images (
                id TEXT PRIMARY KEY, prompt TEXT NOT NULL, model TEXT,
                width INTEGER DEFAULT 1024, height INTEGER DEFAULT 1024,
                image_url TEXT, image_path TEXT, status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def generate(self, prompt: str, model: str = "dall-e-3",
                 width: int = 1024, height: int = 1024) -> Dict:
        """Generate an image from prompt."""
        import uuid
        img_id = str(uuid.uuid4())[:8]
        
        result = {"ok": False, "prompt": prompt, "model": model, "error": ""}
        
        # Try OpenAI DALL-E
        try:
            import openai
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            response = client.images.generate(
                model=model, prompt=prompt, size=f"{width}x{height}", n=1
            )
            if response.data:
                result["ok"] = True
                result["image_url"] = response.data[0].url
        except ImportError:
            result["error"] = "OpenAI SDK not installed"
        except Exception as e:
            result["error"] = str(e)
        
        # Store
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO generated_images (id, prompt, model, width, height, image_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (img_id, prompt[:500], model, width, height,
              result.get("image_url", ""), "success" if result["ok"] else "failed"))
        conn.commit()
        conn.close()
        
        return result

_gen = None
def get_image_generator() -> ImageGenerator:
    global _gen
    if _gen is None: _gen = ImageGenerator()
    return _gen
