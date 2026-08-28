#!/usr/bin/env python3
"""V40.53 — Web Scraping: Firecrawl/Crawl4AI-style extraction."""

import os, sys, json, sqlite3, re, time, hashlib
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/web_scraping.db")

class WebScraper:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scrape_jobs (
                id TEXT PRIMARY KEY, url TEXT NOT NULL, status TEXT DEFAULT 'pending',
                result TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def scrape(self, url: str, extract_type: str = "markdown") -> Dict:
        """Scrape a URL and extract content."""
        import uuid
        job_id = str(uuid.uuid4())[:8]
        
        result = {"ok": False, "url": url, "content": "", "error": ""}
        
        try:
            import urllib.request
            from html.parser import HTMLParser
            
            # Validate URL
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                result["error"] = "Invalid URL scheme"
                return result
            
            # Fetch
            req = urllib.request.Request(url, headers={"User-Agent": "Aeryn/40.53"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            
            if extract_type == "markdown":
                result["content"] = self._html_to_markdown(html)
            elif extract_type == "text":
                result["content"] = self._html_to_text(html)
            else:
                result["content"] = html[:10000]
            
            result["ok"] = True
        except Exception as e:
            result["error"] = str(e)
        
        # Store
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO scrape_jobs (id, url, status, result, error)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, url, "success" if result["ok"] else "failed",
              json.dumps(result)[:5000], result.get("error", "")))
        conn.commit()
        conn.close()
        
        return result
    
    def _html_to_markdown(self, html: str) -> str:
        """Simple HTML to markdown conversion."""
        # Remove script/style
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.I)
        
        # Headers
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', text, flags=re.I)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', text, flags=re.I)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', text, flags=re.I)
        
        # Links
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.I)
        
        # Paragraphs
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\n\1', text, flags=re.I)
        text = re.sub(r'<br[^>]*>', '\n', text, flags=re.I)
        
        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()[:10000]
    
    def _html_to_text(self, html: str) -> str:
        """Extract plain text from HTML."""
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:10000]

_scraper = None
def get_web_scraper() -> WebScraper:
    global _scraper
    if _scraper is None: _scraper = WebScraper()
    return _scraper
