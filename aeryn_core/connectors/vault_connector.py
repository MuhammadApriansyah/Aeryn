#!/usr/bin/env python3
"""V61.1 — Enterprise RAG Connectors (Onyx-style) for Aeryn.

VaultConnector: sync external data sources into Vault.
Supported: filesystem, web URLs, GitHub repos.
"""
import os
import re
import json
import time
import hashlib
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VaultConnector:
    """Base class for external data connectors."""

    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type
        self.stats = {"synced": 0, "skipped": 0, "errors": 0}

    def connect(self) -> bool:
        """Test connection to source."""
        raise NotImplementedError

    def sync(self) -> Dict:
        """Sync data from source to vault."""
        raise NotImplementedError

    def get_stats(self) -> Dict:
        return self.stats


class FileSystemConnector(VaultConnector):
    """Sync local files into Vault."""

    def __init__(self, paths: List[str], extensions: List[str] = None):
        super().__init__("filesystem", "file")
        self.paths = paths
        self.extensions = extensions or [".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml"]

    def connect(self) -> bool:
        return all(os.path.exists(p) for p in self.paths)

    def sync(self) -> Dict:
        from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
        vault = AerynVault()
        
        for base_path in self.paths:
            if os.path.isfile(base_path):
                self._sync_file(vault, base_path)
            elif os.path.isdir(base_path):
                for root, dirs, files in os.walk(base_path):
                    # Skip hidden dirs
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        if any(fname.endswith(ext) for ext in self.extensions):
                            fpath = os.path.join(root, fname)
                            self._sync_file(vault, fpath)
        
        return self.stats

    def _sync_file(self, vault, fpath: str):
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Skip if too large (>100KB)
            if len(content) > 100000:
                self.stats["skipped"] += 1
                return
            
            # Generate unique ID from path + content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            doc_id = f"fs_{hashlib.md5(fpath.encode()).hexdigest()[:12]}_{content_hash}"
            
            # Check if already synced (by title)
            title = os.path.basename(fpath)
            
            entry = VaultEntry(
                layer=LAYER_WIKI,
                title=f"[FS] {title}",
                body=f"Source: {fpath}\n\n{content[:5000]}",
                tags=["connector", "filesystem", f"ext_{os.path.splitext(fpath)[1]}"],
                metadata={"source": fpath, "synced_at": time.time(), "doc_id": doc_id},
            )
            vault.write(entry)
            self.stats["synced"] += 1
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to sync {fpath}: {e}")


class WebConnector(VaultConnector):
    """Sync web URLs into Vault."""

    def __init__(self, urls: List[str], headers: Dict = None):
        super().__init__("web", "url")
        self.urls = urls
        self.headers = headers or {"User-Agent": "Aeryn-Agent/61.1"}

    def connect(self) -> bool:
        try:
            r = requests.head(self.urls[0], headers=self.headers, timeout=5)
            return r.status_code < 400
        except:
            return False

    def sync(self) -> Dict:
        from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
        vault = AerynVault()
        
        for url in self.urls:
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                if r.status_code != 200:
                    self.stats["errors"] += 1
                    continue
                
                content = r.text
                # Strip HTML tags (basic)
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                
                doc_id = f"web_{hashlib.md5(url.encode()).hexdigest()[:16]}"
                title = url.split("/")[-1] or url
                
                entry = VaultEntry(
                    layer=LAYER_WIKI,
                    title=f"[Web] {title[:80]}",
                    body=f"Source: {url}\n\n{content[:5000]}",
                    tags=["connector", "web"],
                    metadata={"source": url, "synced_at": time.time(), "doc_id": doc_id},
                )
                vault.write(entry)
                self.stats["synced"] += 1
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to sync {url}: {e}")
        
        return self.stats


class GitHubConnector(VaultConnector):
    """Sync GitHub repo files into Vault."""

    def __init__(self, repo: str, paths: List[str] = None, token: str = None):
        super().__init__("github", "repo")
        self.repo = repo  # "owner/repo"
        self.paths = paths or [""]
        self.token = token or os.environ.get("GITHUB_TOKEN", "")

    def connect(self) -> bool:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        try:
            r = requests.get(f"https://api.github.com/repos/{self.repo}", headers=headers, timeout=10)
            return r.status_code == 200
        except:
            return False

    def sync(self) -> Dict:
        from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
        vault = AerynVault()
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        for path in self.paths:
            url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code != 200:
                    self.stats["errors"] += 1
                    continue
                
                items = r.json()
                if not isinstance(items, list):
                    items = [items]
                
                for item in items:
                    if item.get("type") == "file" and item.get("name", "").endswith((".md", ".txt", ".py", ".js")):
                        self._sync_file(vault, item, headers)
                    elif item.get("type") == "dir":
                        self.paths.append(item["path"])
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Failed to sync {path}: {e}")
        
        return self.stats

    def _sync_file(self, vault, item: Dict, headers: Dict):
        try:
            download_url = item.get("download_url", "")
            if not download_url:
                return
            
            r = requests.get(download_url, headers=headers, timeout=15)
            if r.status_code != 200:
                self.stats["errors"] += 1
                return
            
            content = r.text
            doc_id = f"gh_{hashlib.md5(item['path'].encode()).hexdigest()[:16]}"
            
            entry = VaultEntry(
                layer=LAYER_WIKI,
                title=f"[GH] {item['path']}",
                body=f"Source: {self.repo}/{item['path']}\n\n{content[:5000]}",
                tags=["connector", "github", self.repo.replace("/", "_")],
                metadata={"source": item["path"], "synced_at": time.time(), "doc_id": doc_id},
            )
            vault.write(entry)
            self.stats["synced"] += 1
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to sync {item.get('path')}: {e}")


class ConnectorManager:
    """Manage all connectors."""

    def __init__(self):
        self._connectors: Dict[str, VaultConnector] = {}

    def register(self, connector: VaultConnector):
        self._connectors[connector.name] = connector
        return connector

    def get(self, name: str) -> Optional[VaultConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[str]:
        return list(self._connectors.keys())

    def sync_all(self) -> Dict:
        results = {}
        for name, connector in self._connectors.items():
            try:
                stats = connector.sync()
                results[name] = stats
            except Exception as e:
                results[name] = {"error": str(e)}
        return results

    def sync_one(self, name: str) -> Dict:
        connector = self._connectors.get(name)
        if not connector:
            return {"error": f"Connector not found: {name}"}
        return connector.sync()


# Singleton
_manager = None

def get_connector_manager() -> ConnectorManager:
    global _manager
    if _manager is None:
        _manager = ConnectorManager()
    return _manager
