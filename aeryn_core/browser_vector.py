#!/usr/bin/env python3
"""V40.51-V40.52 — Browser Automation + Vector DB (inline)."""

# === BROWSER AUTOMATION ===
import os, sys, json, sqlite3, subprocess, time
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "browser.db")

class BrowserSession:
    def __init__(self, headless: bool = True, proxy: str = None):
        self.headless = headless
        self.proxy = proxy
        self._driver = None
        self._playwright = None
    
    def start(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            browser = self._playwright.chromium.launch(headless=self.headless)
            self._driver = browser.new_context()
            return True
        except ImportError:
            pass
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            if self.headless:
                opts.add_argument("--headless")
            self._driver = webdriver.Chrome(options=opts)
            return True
        except ImportError:
            return False
    
    def navigate(self, url: str) -> bool:
        try:
            if hasattr(self._driver, 'goto'):
                self._driver.goto(url)
            else:
                self._driver.new_page().goto(url)
            return True
        except Exception:
            return False
    
    def click(self, selector: str) -> bool:
        try:
            if hasattr(self._driver, 'click'):
                self._driver.click(selector)
            return True
        except Exception:
            return False
    
    def fill(self, selector: str, text: str) -> bool:
        try:
            if hasattr(self._driver, 'fill'):
                self._driver.fill(selector, text)
            return True
        except Exception:
            return False
    
    def screenshot(self, path: str = "/tmp/screenshot.png") -> str:
        try:
            if hasattr(self._driver, 'screenshot'):
                self._driver.screenshot(path=path)
                return path
        except Exception:
            pass
        return ""
    
    def extract_text(self) -> str:
        try:
            if hasattr(self._driver, 'content'):
                return self._driver.content()
        except Exception:
            pass
        return ""
    
    def close(self):
        try:
            if self._driver:
                if hasattr(self._driver, 'close'):
                    self._driver.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

class BrowserAutomation:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS browser_sessions (
                id TEXT PRIMARY KEY, user_id TEXT, url TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP, ended_at TEXT
            );
            CREATE TABLE IF NOT EXISTS browser_actions (
                id TEXT PRIMARY KEY, session_id TEXT, action_type TEXT,
                selector TEXT, value TEXT, success INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def create_session(self, user_id: str, url: str = "") -> str:
        import uuid
        sid = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO browser_sessions (id, user_id, url) VALUES (?,?,?)",
                     (sid, user_id, url))
        conn.commit()
        conn.close()
        return sid
    
    def run_task(self, url: str, actions: List[Dict], user_id: str = "default") -> Dict:
        """Run a browser automation task."""
        session_id = self.create_session(user_id, url)
        session = BrowserSession(headless=True)
        results = {"session_id": session_id, "steps": [], "ok": False}
        
        if not session.start():
            results["error"] = "Browser not available (install playwright or selenium)"
            return results
        
        try:
            if not session.navigate(url):
                results["error"] = f"Failed to navigate to {url}"
                return results
            
            for i, action in enumerate(actions):
                action_type = action.get("type", "")
                success = False
                
                if action_type == "click":
                    success = session.click(action.get("selector", ""))
                elif action_type == "fill":
                    success = session.fill(action.get("selector", ""), action.get("value", ""))
                elif action_type == "screenshot":
                    path = session.screenshot(action.get("path", f"/tmp/screenshot_{i}.png"))
                    success = bool(path)
                elif action_type == "wait":
                    time.sleep(action.get("seconds", 1))
                    success = True
                
                results["steps"].append({"action": action_type, "success": success})
            
            results["ok"] = True
            results["content"] = session.extract_text()[:5000]
        finally:
            session.close()
        
        return results

_browser = None
def get_browser() -> BrowserAutomation:
    global _browser
    if _browser is None: _browser = BrowserAutomation()
    return _browser


# === VECTOR DB ===
VEC_DB_PATH = os.path.join(DATABASE_DIR, "vector.db")

class VectorDB:
    def __init__(self, db_path: str = VEC_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT PRIMARY KEY, dimension INTEGER DEFAULT 384,
                description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY, collection TEXT NOT NULL,
                vector TEXT NOT NULL, text TEXT, metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection) REFERENCES collections(name)
            );
            CREATE INDEX IF NOT EXISTS idx_emb_coll ON embeddings(collection);
        """)
        conn.commit()
        conn.close()
    
    def create_collection(self, name: str, dimension: int = 384,
                          description: str = "") -> str:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO collections (name, dimension, description)
            VALUES (?, ?, ?)
        """, (name, dimension, description))
        conn.commit()
        conn.close()
        return name
    
    def add(self, collection: str, texts: List[str],
            embeddings: List[List[float]] = None, metadatas: List[Dict] = None) -> List[str]:
        import uuid
        
        if embeddings is None:
            embeddings = [[0.0] * 384 for _ in texts]
        
        ids = []
        conn = sqlite3.connect(self.db_path)
        for i, text in enumerate(texts):
            eid = str(uuid.uuid4())[:8]
            conn.execute("""
                INSERT INTO embeddings (id, collection, vector, text, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (eid, collection, json.dumps(embeddings[i]), text[:2000],
                  json.dumps(metadatas[i] if metadatas else {})))
            ids.append(eid)
        conn.commit()
        conn.close()
        return ids
    
    def search(self, collection: str, query_embedding: List[float],
               limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT id, vector, text, metadata FROM embeddings
            WHERE collection = ?
        """, (collection,)).fetchall()
        conn.close()
        
        # Simple cosine similarity
        import math
        
        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            if mag_a * mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)
        
        results = []
        for row in rows:
            vec = json.loads(row[1])
            score = cosine(query_embedding, vec)
            results.append({
                "id": row[0],
                "score": score,
                "text": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def delete_collection(self, name: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM embeddings WHERE collection=?", (name,))
        conn.execute("DELETE FROM collections WHERE name=?", (name,))
        conn.commit()
        conn.close()
        return True

_vdb = None
def get_vector_db() -> VectorDB:
    global _vdb
    if _vdb is None: _vdb = VectorDB()
    return _vdb
