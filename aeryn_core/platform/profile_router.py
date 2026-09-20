#!/usr/bin/env python3
"""V62.5 — FW6: Multi-user profile routing (satu Aeryn, banyak user).

Ala Hermes-multiplex: setiap user (platform) route ke profil terisolasi —
memori, sesi, tool-permission per user. Layer di atas AuthManager +
session_store (yang sudah user-isolated).
Real APIs only — no test doubles.
"""

import os
import sys
import json
import sqlite3
import uuid
from typing import Dict, List, Optional

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
DB_PATH = os.environ.get(
    "AERYN_PROFILES_DB", os.path.join(HOME, "aeryn-core-agent", "Personalisasi", "Database", "profiles.db")
)


class ProfileRouter:
    """Route users ke profil terisolasi (memori/sesi/permissions per user)."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                display_name TEXT,
                platform TEXT DEFAULT 'api',
                role TEXT DEFAULT 'member',
                home_channel TEXT,
                memory_scope TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS profile_routes (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                platform_chat_id TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id),
                UNIQUE(platform, platform_chat_id)
            );
        """)
        conn.commit()
        conn.close()

    # ── Profile CRUD ──

    def create_profile(self, user_id: str, display_name: Optional[str] = None,
                       platform: str = "api", role: str = "member",
                       home_channel: Optional[str] = None) -> str:
        """Buat profil untuk satu user. user_id = identity unik."""
        pid = uuid.uuid4().hex[:8]
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO profiles (id, user_id, display_name, platform, role, home_channel, memory_scope) "
                "VALUES (?,?,?,?,?,?,?)",
                (pid, user_id, display_name or user_id, platform, role, home_channel, user_id),
            )
            conn.commit()
        finally:
            conn.close()
        return pid

    def get_profile(self, user_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM profiles WHERE user_id=? AND is_active=1", (user_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_profiles(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM profiles WHERE is_active=1 ORDER BY created_at"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def set_active(self, user_id: str, active: bool) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "UPDATE profiles SET is_active=? WHERE user_id=?",
                (1 if active else 0, user_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    # ── Routing: platform chat → profile ──

    def bind_route(self, platform: str, platform_chat_id: str, user_id: str) -> str:
        """Bind platform chat (mis. whatsapp:+62812...) ke profil user."""
        profile = self.get_profile(user_id)
        if not profile:
            raise ValueError(f"Profile tidak ada: {user_id}")
        rid = uuid.uuid4().hex[:8]
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO profile_routes (id, platform, platform_chat_id, profile_id) "
                "VALUES (?,?,?,?)",
                (rid, platform, platform_chat_id, profile["id"]),
            )
            conn.commit()
        finally:
            conn.close()
        return rid

    def resolve(self, platform: str, platform_chat_id: str) -> Optional[Dict]:
        """Resolve platform chat → profil (untuk gateway multiplexing)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT p.* FROM profile_routes r JOIN profiles p ON p.id = r.profile_id "
                "WHERE r.platform=? AND r.platform_chat_id=? AND p.is_active=1",
                (platform, platform_chat_id),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        try:
            profiles = conn.execute("SELECT COUNT(*) FROM profiles WHERE is_active=1").fetchone()[0]
            routes = conn.execute("SELECT COUNT(*) FROM profile_routes").fetchone()[0]
            by_platform = conn.execute(
                "SELECT platform, COUNT(*) FROM profiles WHERE is_active=1 GROUP BY platform"
            ).fetchall()
            return {
                "profiles": profiles,
                "routes": routes,
                "by_platform": {p: c for p, c in by_platform},
            }
        finally:
            conn.close()


_router = None


def get_profile_router() -> ProfileRouter:
    global _router
    if _router is None:
        _router = ProfileRouter()
    return _router


def register(registry) -> None:
    """Register FW6 profile tools into the PluginRegistry."""
    router = get_profile_router()

    registry.register(
        "profile_create",
        "Buat profil user baru (satu Aeryn, banyak user — terisolasi)",
        handler=lambda user_id, display_name=None, platform="api", **kw: {
            "ok": True, "profile_id": router.create_profile(
                user_id, display_name if display_name else None, platform),
        },
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "display_name": {"type": "string"},
                "platform": {"type": "string"},
            },
            "required": ["user_id"],
        },
        tags=["profile", "user", "multi-user"],
        category="admin",
    )
    registry.register(
        "profile_list",
        "List semua profil user aktif",
        handler=lambda **kw: {"ok": True, "profiles": router.list_profiles()},
        parameters={"type": "object", "properties": {}},
        tags=["profile", "user", "list"],
        category="admin",
    )
    registry.register(
        "profile_bind",
        "Bind platform chat ke profil user (routing multiplex)",
        handler=lambda platform, platform_chat_id, user_id, **kw: {
            "ok": True, "route_id": router.bind_route(platform, platform_chat_id, user_id),
        },
        parameters={
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "platform_chat_id": {"type": "string"},
                "user_id": {"type": "string"},
            },
            "required": ["platform", "platform_chat_id", "user_id"],
        },
        tags=["profile", "route", "gateway"],
        category="admin",
    )
    registry.register(
        "profile_resolve",
        "Resolve platform chat → profil (cek routing)",
        handler=lambda platform, platform_chat_id, **kw: {
            "ok": True, "profile": router.resolve(platform, platform_chat_id),
        },
        parameters={
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "platform_chat_id": {"type": "string"},
            },
            "required": ["platform", "platform_chat_id"],
        },
        tags=["profile", "route", "resolve"],
        category="admin",
    )
    registry.register(
        "profile_stats",
        "Multi-user profile stats (profiles/routes/platforms)",
        handler=lambda **kw: {"ok": True, **router.stats()},
        parameters={"type": "object", "properties": {}},
        tags=["profile", "stats"],
        category="admin",
    )
