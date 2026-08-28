#!/usr/bin/env python3
"""V40.46 — LLM Fine-tuning: Dataset prep and training orchestration."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/finetuning.db")

class FinetuningManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS training_datasets (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT,
                data_path TEXT, format TEXT DEFAULT 'jsonl',
                status TEXT DEFAULT 'ready', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS training_jobs (
                id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, model_name TEXT,
                provider TEXT, status TEXT DEFAULT 'pending',
                started_at TEXT, completed_at TEXT, result TEXT, error TEXT
            );
            CREATE TABLE IF NOT EXISTS model_registry (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, provider TEXT,
                model_id TEXT, base_model TEXT, status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def create_dataset(self, name: str, data_path: str,
                       description: str = "", format: str = "jsonl") -> str:
        import uuid
        ds_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO training_datasets (id, name, description, data_path, format)
            VALUES (?, ?, ?, ?, ?)
        """, (ds_id, name, description, data_path, format))
        conn.commit()
        conn.close()
        return ds_id
    
    def start_training(self, dataset_id: str, model_name: str,
                       provider: str = "openai") -> str:
        import uuid
        job_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO training_jobs (id, dataset_id, model_name, provider, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (job_id, dataset_id, model_name, provider))
        conn.commit()
        conn.close()
        return job_id
    
    def list_models(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM model_registry WHERE status='active'").fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "provider": r[2], "model_id": r[3]} for r in rows]

_ft = None
def get_finetuning() -> FinetuningManager:
    global _ft
    if _ft is None: _ft = FinetuningManager()
    return _ft
