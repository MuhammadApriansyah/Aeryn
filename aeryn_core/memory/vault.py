"""V39.16 — Aeryn Vault: Obsidian-style memory architecture.

Layers:
  Raw/         — unprocessed inputs (transcripts, outputs, findings)
  Wiki/        — synthesized, atomic knowledge (one idea per file)
  Projects/    — active project deliverables
  System/      — identity, skills, config (always loaded)
  Daily/       — daily logs, plans, retrospectives
"""
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, List, Dict
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

BASE = VAULT_DIR

SUBDIRS = ["Raw", "Wiki", "Projects", "System", "Daily", "Skills"]

LAYER_RAW = "Raw"
LAYER_WIKI = "Wiki"
LAYER_PROJECTS = "Projects"
LAYER_SYSTEM = "System"
LAYER_DAILY = "Daily"
LAYER_SKILLS = "Skills"


def ensure_dirs():
    """Create vault directory structure if missing."""
    for sub in SUBDIRS:
        os.makedirs(os.path.join(BASE, sub), exist_ok=True)


def file_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:12]


class VaultEntry:
    """Single atomic knowledge entry."""
    def __init__(self, layer: str, title: str, body: str, tags: list = None, links: list = None, author: str = "aeryn"):
        self.layer = layer
        self.title = title.strip()[:100]
        self.body = body.strip()
        self.tags = tags or []
        self.links = links or []
        self.author = author  # V39.44: author attribution (multi-agent support)
        self.created = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        self.updated = self.created
        self.hash = file_hash(title + body[:200])
    
    @property
    def filename(self) -> str:
        safe = self.title.lower().replace(" ", "_")[:60]
        return f"{safe}__{self.hash}.md"
    
    @property
    def path(self) -> str:
        return os.path.join(BASE, self.layer, self.filename)
    
    @property
    def frontmatter(self) -> str:
        tags_str = ", ".join(self.tags)
        links_str = ", ".join(self.links)
        return (
            f"---\n"
            f"title: {self.title}\n"
            f"author: {self.author}\n"
            f"tags: [{tags_str}]\n"
            f"links: [{links_str}]\n"
            f"created: {self.created}\n"
            f"updated: {self.updated}\n"
            f"hash: {self.hash}\n"
            f"---\n"
        )
    
    def to_markdown(self) -> str:
        return self.frontmatter + "\n" + self.body + "\n"


class AerynVault:
    """Main vault interface for Aeryn."""
    
    def __init__(self):
        ensure_dirs()
        self._cache = {}
    
    def write(self, entry: VaultEntry) -> str:
        """Write entry to vault. Returns path."""
        path = entry.path
        with open(path, "w", encoding="utf-8") as f:
            f.write(entry.to_markdown())
        self._cache[entry.hash] = entry
        return path
    
    def read(self, path: str) -> str:
        """Read entry content."""
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""
    
    def search(self, query: str, layer: str = None, limit: int = 10) -> list:
        """Simple search across vault (V39.60: added cache)."""
        # V39.60: Check cache
        cache_key = f"{query}:{layer}:{limit}"
        if hasattr(self, '_search_cache') and cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        if not hasattr(self, '_search_cache'):
            self._search_cache = {}
        
        results = []
        query_lower = query.lower()
        
        search_layers = [layer] if layer else SUBDIRS
        
        for sub in search_layers:
            dirpath = os.path.join(BASE, sub)
            if not os.path.isdir(dirpath):
                continue
            for fname in os.listdir(dirpath):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        content = f.read()
                    if query_lower in content.lower():
                        results.append({"path": fpath, "layer": sub, "preview": content[:200]})
                        if len(results) >= limit:
                            self._search_cache[cache_key] = results
                            return results
                except OSError:
                    continue
        
        self._search_cache[cache_key] = results
        return results
    
    def list_layer(self, layer: str) -> list:
        """List all entries in a layer."""
        dirpath = os.path.join(BASE, layer)
        if not os.path.isdir(dirpath):
            return []
        return [f for f in os.listdir(dirpath) if f.endswith(".md")]
    
    def get_daily_today(self) -> str:
        """Get today's daily note, or create one."""
        today = time.strftime("%Y-%m-%d")
        dirpath = os.path.join(BASE, LAYER_DAILY)
        os.makedirs(dirpath, exist_ok=True)
        
        # Find existing daily for today
        if os.path.isdir(dirpath):
            for fname in os.listdir(dirpath):
                if fname.startswith("daily__") and today in fname and fname.endswith(".md"):
                    return self.read(os.path.join(dirpath, fname))
        
        # Create new daily
        entry = VaultEntry(
            layer=LAYER_DAILY,
            title=f"Daily {today}",
            body=f"# {today}\n\n## Plan\n- \n\n## Log\n\n## Retrospective\n",
            tags=["daily", today],
        )
        self.write(entry)
        return self.read(entry.path)
    
    def append_daily(self, section: str, content: str):
        """Append content to today's daily note."""
        today = time.strftime("%Y-%m-%d")
        dirpath = os.path.join(BASE, LAYER_DAILY)
        os.makedirs(dirpath, exist_ok=True)
        
        # Find existing daily for today
        existing_path = None
        if os.path.isdir(dirpath):
            for fname in os.listdir(dirpath):
                if fname.startswith("daily__") and today in fname and fname.endswith(".md"):
                    existing_path = os.path.join(dirpath, fname)
                    break
        
        if existing_path is None:
            entry = VaultEntry(
                layer=LAYER_DAILY,
                title=f"Daily {today}",
                body=f"# {today}\n\n## {section}\n- {content}\n",
                tags=["daily", today],
            )
            self.write(entry)
        else:
            existing = self.read(existing_path)
            lines = existing.split("\n")
            new_lines = []
            in_section = False
            inserted = False
            for line in lines:
                new_lines.append(line)
                if line.strip().lower() == f"## {section.lower()}":
                    in_section = True
                elif in_section and line.startswith("## "):
                    new_lines.insert(-1, f"- {content}")
                    inserted = True
                    in_section = False
            if in_section and not inserted:
                new_lines.append(f"- {content}")
            with open(existing_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
    
    def count_entries(self) -> dict:
        """Count entries per layer."""
        counts = {}
        for sub in SUBDIRS:
            dirpath = os.path.join(BASE, sub)
            if os.path.isdir(dirpath):
                counts[sub] = len([f for f in os.listdir(dirpath) if f.endswith(".md")])
            else:
                counts[sub] = 0
        return counts
    
    def list_entries(self, layer: str = None, limit: int = 10, offset: int = 0) -> list:
        """List vault entries with pagination."""
        entries = []
        search_layers = [layer] if layer else SUBDIRS
        
        for sub in search_layers:
            dirpath = os.path.join(BASE, sub)
            if not os.path.isdir(dirpath):
                continue
            for fname in sorted(os.listdir(dirpath)):
                if not fname.endswith(".md"):
                    continue
                filepath = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(filepath)
                    with open(filepath, encoding="utf-8") as f:
                        body = f.read()
                    # Extract tags from frontmatter
                    tags = []
                    if body.startswith("---"):
                        try:
                            end = body.index("---", 3)
                            fm = body[3:end].strip()
                            for line in fm.split("\n"):
                                if line.strip().startswith("tags:"):
                                    tags = [t.strip() for t in line.split(":")[1].strip().strip("[]").split(",") if t.strip()]
                        except Exception:
                            pass
                    entries.append({
                        "id": fname.replace(".md", ""),
                        "title": fname.replace(".md", "").replace("-", " ").replace("_", " ").title(),
                        "layer": sub,
                        "tags": tags,
                        "created_at": stat.st_mtime,
                        "size": stat.st_size,
                    })
                except Exception:
                    pass
        
        # Sort by created_at desc
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        return entries[offset:offset + limit]
    
    def get_entry(self, entry_id: str) -> Optional[dict]:
        """Get single vault entry by ID (filename without .md)."""
        for sub in SUBDIRS:
            dirpath = os.path.join(BASE, sub)
            if not os.path.isdir(dirpath):
                continue
            for fname in os.listdir(dirpath):
                if not fname.endswith(".md"):
                    continue
                if fname.replace(".md", "") == entry_id:
                    filepath = os.path.join(dirpath, fname)
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            body = f.read()
                        return {
                            "id": entry_id,
                            "title": fname.replace(".md", "").replace("-", " ").replace("_", " ").title(),
                            "layer": sub,
                            "body": body,
                        }
                    except Exception:
                        pass
        return None
    
    def render_summary(self) -> str:
        """Render vault summary for system prompt injection."""
        counts = self.count_entries()
        parts = ["## VAULT STATE"]
        for layer, count in counts.items():
            parts.append(f"- {layer}: {count} entries")
        
        # Recent daily
        today = time.strftime("%Y-%m-%d")
        daily_path = os.path.join(BASE, LAYER_DAILY, f"daily__{today}.md")
        if os.path.exists(daily_path):
            daily = self.read(daily_path)
            parts.append(f"\n## TODAY'S PLAN ({today})")
            for line in daily.split("\n"):
                if line.startswith("## ") or line.startswith("- "):
                    parts.append(line)
        
        return "\n".join(parts)


# Singleton
_vault = None

def get_vault() -> AerynVault:
    global _vault
    if _vault is None:
        _vault = AerynVault()
    return _vault
