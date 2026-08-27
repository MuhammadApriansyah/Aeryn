#!/usr/bin/env python3
"""V39.75 — Memory Indexing: Index vault entries into semantic search.

Scans vault entries and indexes them into the semantic search engine.
Run periodically to keep search up to date.
"""

import os
import sys
import json
import time
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.vault import AerynVault, LAYER_WIKI, LAYER_PROJECTS, LAYER_DAILY, SUBDIRS
from aeryn_core.semantic_search import get_semantic_search
from aeryn_core.config import VAULT_DIR

def index_vault(batch_size: int = 100) -> Dict:
    """Index all vault entries into semantic search."""
    vault = AerynVault()
    search = get_semantic_search()
    
    results = {
        "indexed": 0,
        "skipped": 0,
        "errors": 0,
        "layers": {},
    }
    
    for layer in SUBDIRS:
        dirpath = os.path.join(VAULT_DIR, layer)
        if not os.path.isdir(dirpath):
            continue
        
        layer_count = 0
        for fname in os.listdir(dirpath):
            if not fname.endswith(".md"):
                continue
            
            fpath = os.path.join(dirpath, fname)
            memory_id = f"{layer}/{fname}"
            
            # Skip if already indexed
            existing = search.search(fname.replace('.md', ''), limit=1)
            if any(r.get("memory_id") == memory_id for r in existing):
                results["skipped"] += 1
                continue
            
            try:
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                
                # Extract title from first heading
                title = fname.replace('.md', '')
                for line in content.split('\n'):
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
                
                search.index_memory(
                    memory_id=memory_id,
                    title=title,
                    content=content[:3000],
                    source="vault",
                    author="aeryn",
                    metadata={"layer": layer, "file": fname}
                )
                
                results["indexed"] += 1
                layer_count += 1
                
            except Exception as e:
                results["errors"] += 1
        
        if layer_count > 0:
            results["layers"][layer] = layer_count
    
    return results

def index_via_shared_db() -> Dict:
    """Index reminders and tasks from shared DB."""
    from aeryn_core.shared_db import get_shared_db
    db = get_shared_db()
    search = get_semantic_search()
    
    indexed = 0
    
    # Index reminders
    reminders = db.get_all_reminders()
    for r in reminders:
        memory_id = f"reminder/{r['id']}"
        search.index_memory(
            memory_id=memory_id,
            title=f"Reminder: {r['text'][:50]}",
            content=r['text'],
            source="reminder",
            author=r.get('source', 'aeryn'),
            metadata={"due": r.get('due_at'), "status": r.get('status')}
        )
        indexed += 1
    
    # Index tasks
    tasks = db.get_pending_tasks()
    for t in tasks:
        memory_id = f"task/{t['id']}"
        search.index_memory(
            memory_id=memory_id,
            title=f"Task: {t['title']}",
            content=t.get('description', ''),
            source="task",
            author="aeryn",
            metadata={"priority": t.get('priority'), "status": t.get('status', 'pending')}
        )
        indexed += 1
    
    return {"indexed": indexed}

if __name__ == "__main__":
    print("=== Memory Indexing ===")
    
    # Index vault
    print("\n1. Indexing vault...")
    results = index_vault()
    print(f"   Indexed: {results['indexed']}")
    print(f"   Skipped (already indexed): {results['skipped']}")
    print(f"   Errors: {results['errors']}")
    print(f"   Layers: {results['layers']}")
    
    # Index shared DB
    print("\n2. Indexing shared DB...")
    db_results = index_via_shared_db()
    print(f"   Indexed: {db_results['indexed']}")
    
    # Show stats
    search = get_semantic_search()
    stats = search.get_stats()
    print(f"\n3. Semantic search stats: {json.dumps(stats, indent=2)}")
