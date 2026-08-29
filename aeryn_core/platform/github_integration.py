#!/usr/bin/env python3
"""V40.40 — GitHub Integration: Issues, PR, CI/CD, code review."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "github_integration.db")

class GitHubIntegration:
    def __init__(self, token: str = None, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS github_repos (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, repo_name TEXT NOT NULL,
                full_name TEXT NOT NULL, is_active INTEGER DEFAULT 1,
                last_sync TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS github_issues (
                id TEXT PRIMARY KEY, repo_id TEXT NOT NULL, issue_number INTEGER,
                title TEXT NOT NULL, body TEXT, state TEXT DEFAULT 'open',
                labels TEXT DEFAULT '[]', assignee TEXT, created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS github_prs (
                id TEXT PRIMARY KEY, repo_id TEXT NOT NULL, pr_number INTEGER,
                title TEXT NOT NULL, body TEXT, state TEXT DEFAULT 'open',
                branch TEXT, base_branch TEXT, created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS github_actions (
                id TEXT PRIMARY KEY, repo_id TEXT NOT NULL, workflow_name TEXT,
                status TEXT, conclusion TEXT, run_id TEXT, created_at TEXT
            );
        """)
        conn.commit()
        conn.close()
    
    def create_issue(self, repo_id: str, title: str, body: str = "",
                     labels: List[str] = None) -> str:
        import uuid
        issue_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO github_issues (id, repo_id, title, body, labels)
            VALUES (?, ?, ?, ?, ?)
        """, (issue_id, repo_id, title, body, json.dumps(labels or [])))
        conn.commit()
        conn.close()
        return issue_id
    
    def link_issue_to_pr(self, issue_id: str, pr_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE github_prs SET body = body || ? WHERE id = ?",
                     (f"\n\nCloses #{issue_id}", pr_id))
        conn.commit()
        conn.close()

_gh = None
def get_github() -> GitHubIntegration:
    global _gh
    if _gh is None: _gh = GitHubIntegration()
    return _gh

if __name__ == "__main__":
    gh = get_github()
    print("GitHub integration ready")
