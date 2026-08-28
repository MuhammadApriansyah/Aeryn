#!/usr/bin/env python3
"""V40.41 — Data Encryption: At-rest encryption for sensitive data."""

import os, sys, json, sqlite3, hashlib, base64
from typing import Dict, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/encryption.db")

class DataEncryption:
    def __init__(self, key: str = None, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.key = key or os.environ.get("ENCRYPTION_KEY", "aeryn-default-key-2026")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS encrypted_data (
                id TEXT PRIMARY KEY, data_type TEXT NOT NULL, encrypted_blob TEXT NOT NULL,
                data_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, expires_at TEXT
            );
            CREATE TABLE IF NOT EXISTS encryption_keys (
                id TEXT PRIMARY KEY, key_hash TEXT NOT NULL, purpose TEXT,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def encrypt(self, data: str) -> str:
        """Simple XOR encryption with key (use proper crypto in production)."""
        key_bytes = self.key.encode()
        data_bytes = data.encode()
        encrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes)])
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        key_bytes = self.key.encode()
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode()
    
    def encrypt_file(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            data = f.read()
        key_bytes = self.key.encode()
        encrypted = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
        enc_path = file_path + ".enc"
        with open(enc_path, "wb") as f:
            f.write(base64.b64encode(encrypted))
        return enc_path

_enc = None
def get_encryption() -> DataEncryption:
    global _enc
    if _enc is None: _enc = DataEncryption()
    return _enc

if __name__ == "__main__":
    enc = get_encryption()
    test = "Hello secret data"
    encrypted = enc.encrypt(test)
    decrypted = enc.decrypt(encrypted)
    print(f"Test: {test == decrypted}")
