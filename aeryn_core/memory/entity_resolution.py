#!/usr/bin/env python3
"""V40.7 — Entity Resolution: Merge duplicate entities, canonical IDs.

Features:
- Fuzzy matching for entity names
- Canonical entity IDs
- Cross-reference resolution
- Merge duplicate memories
"""

import os
import sys
import json
import re
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(DATABASE_DIR, "entity_resolution.db")


class EntityResolver:
    """Resolve and merge duplicate entities."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS canonical_entities (
                    id TEXT PRIMARY KEY,
                    canonical_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    aliases TEXT DEFAULT '[]',
                    properties TEXT DEFAULT '{}',
                    confidence REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS entity_aliases (
                    alias TEXT PRIMARY KEY,
                    canonical_id TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    FOREIGN KEY (canonical_id) REFERENCES canonical_entities(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_alias ON entity_aliases(alias);
                CREATE INDEX IF NOT EXISTS idx_canonical_type ON canonical_entities(entity_type);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        # Lowercase
        normalized = name.lower().strip()
        
        # Remove common prefixes/titles
        prefixes = ["bu ", "pak ", "mas ", "mbak ", "dik ", "bang ", "kak "]
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two entity names."""
        n1 = self.normalize_name(name1)
        n2 = self.normalize_name(name2)
        
        # Exact match
        if n1 == n2:
            return 1.0
        
        # Substring match
        if n1 in n2 or n2 in n1:
            return 0.9
        
        # Levenshtein-like similarity (simple version)
        # Count matching characters
        common = set(n1) & set(n2)
        total = set(n1) | set(n2)
        
        if not total:
            return 0.0
        
        return len(common) / len(total)
    
    def register_entity(self, name: str, entity_type: str,
                        properties: Dict = None) -> str:
        """Register a new entity or merge with existing."""
        normalized = self.normalize_name(name)
        
        # Check for existing similar entity
        existing = self._find_similar(normalized, entity_type)
        
        if existing:
            # Merge
            canonical_id = existing["id"]
            self._add_alias(canonical_id, normalized)
            return canonical_id
        
        # Create new canonical entity
        import uuid
        canonical_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO canonical_entities (id, canonical_name, entity_type, aliases, properties)
                VALUES (?, ?, ?, ?, ?)
            """, (canonical_id, normalized, entity_type, json.dumps([normalized]),
                  json.dumps(properties or {})))
            
            conn.execute("""
                INSERT INTO entity_aliases (alias, canonical_id, confidence)
                VALUES (?, ?, 1.0)
            """, (normalized, canonical_id))
            
            conn.commit()
        finally:
            conn.close()
        
        return canonical_id
    
    def resolve(self, name: str, entity_type: str = None) -> Optional[Dict]:
        """Resolve an entity name to its canonical form."""
        normalized = self.normalize_name(name)
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Direct alias match
            row = conn.execute("""
                SELECT ce.id, ce.canonical_name, ce.entity_type, ce.aliases, ce.properties
                FROM entity_aliases ea
                JOIN canonical_entities ce ON ea.canonical_id = ce.id
                WHERE ea.alias = ?
            """, (normalized,)).fetchone()
            
            if row:
                return {
                    "id": row[0],
                    "canonical_name": row[1],
                    "entity_type": row[2],
                    "aliases": json.loads(row[3]) if row[3] else [],
                    "properties": json.loads(row[4]) if row[4] else {},
                }
            
            # Fuzzy match
            if entity_type:
                rows = conn.execute("""
                    SELECT id, canonical_name, entity_type, aliases, properties
                    FROM canonical_entities WHERE entity_type = ?
                """, (entity_type,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, canonical_name, entity_type, aliases, properties
                    FROM canonical_entities
                """).fetchall()
            
            best_match = None
            best_score = 0.0
            
            for row in rows:
                score = self.similarity(name, row[1])
                if score > best_score and score > 0.7:
                    best_score = score
                    best_match = {
                        "id": row[0],
                        "canonical_name": row[1],
                        "entity_type": row[2],
                        "aliases": json.loads(row[3]) if row[3] else [],
                        "properties": json.loads(row[4]) if row[4] else {},
                        "similarity": score,
                    }
            
            return best_match
        finally:
            conn.close()
    
    def _find_similar(self, name: str, entity_type: str) -> Optional[Dict]:
        """Find similar existing entity."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, canonical_name, entity_type, aliases, properties
                FROM canonical_entities WHERE entity_type = ?
            """, (entity_type,)).fetchall()
            
            for row in rows:
                score = self.similarity(name, row[1])
                if score > 0.8:
                    return {
                        "id": row[0],
                        "canonical_name": row[1],
                        "entity_type": row[2],
                    }
            return None
        finally:
            conn.close()
    
    def _add_alias(self, canonical_id: str, alias: str):
        """Add an alias to existing entity."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if alias exists
            row = conn.execute(
                "SELECT alias FROM entity_aliases WHERE alias = ?", (alias,)
            ).fetchone()
            
            if not row:
                conn.execute("""
                    INSERT OR IGNORE INTO entity_aliases (alias, canonical_id)
                    VALUES (?, ?)
                """, (alias, canonical_id))
                
                # Update aliases list in canonical entity
                row = conn.execute(
                    "SELECT aliases FROM canonical_entities WHERE id = ?",
                    (canonical_id,)
                ).fetchone()
                
                if row:
                    aliases = json.loads(row[0]) if row[0] else []
                    if alias not in aliases:
                        aliases.append(alias)
                        conn.execute("""
                            UPDATE canonical_entities SET aliases = ?, updated_at = ?
                            WHERE id = ?
                        """, (json.dumps(aliases), datetime.now().isoformat(), canonical_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def merge_entities(self, entity_ids: List[str]) -> Optional[str]:
        """Merge multiple entities into one."""
        if len(entity_ids) < 2:
            return entity_ids[0] if entity_ids else None
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Get all entities
            entities = []
            for eid in entity_ids:
                row = conn.execute("""
                    SELECT id, canonical_name, entity_type, aliases, properties
                    FROM canonical_entities WHERE id = ?
                """, (eid,)).fetchone()
                if row:
                    entities.append(row)
            
            if not entities:
                return None
            
            # Use first entity as canonical
            canonical = entities[0]
            canonical_id = canonical[0]
            
            # Merge aliases and properties
            all_aliases = set()
            all_properties = {}
            
            for entity in entities:
                aliases = json.loads(entity[3]) if entity[3] else []
                all_aliases.update(aliases)
                
                props = json.loads(entity[4]) if entity[4] else {}
                all_properties.update(props)
            
            # Update canonical entity
            conn.execute("""
                UPDATE canonical_entities
                SET aliases = ?, properties = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(list(all_aliases)), json.dumps(all_properties),
                  datetime.now().isoformat(), canonical_id))
            
            # Redirect aliases from merged entities
            for entity in entities[1:]:
                conn.execute("""
                    UPDATE entity_aliases SET canonical_id = ? WHERE canonical_id = ?
                """, (canonical_id, entity[0]))
                conn.execute("DELETE FROM canonical_entities WHERE id = ?", (entity[0],))
            
            conn.commit()
            return canonical_id
        finally:
            conn.close()
    
    def get_all_entities(self, entity_type: str = None) -> List[Dict]:
        """Get all canonical entities."""
        conn = sqlite3.connect(self.db_path)
        try:
            if entity_type:
                rows = conn.execute("""
                    SELECT id, canonical_name, entity_type, aliases, properties, confidence
                    FROM canonical_entities WHERE entity_type = ?
                """, (entity_type,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, canonical_name, entity_type, aliases, properties, confidence
                    FROM canonical_entities
                """).fetchall()
            
            return [
                {
                    "id": r[0],
                    "canonical_name": r[1],
                    "entity_type": r[2],
                    "aliases": json.loads(r[3]) if r[3] else [],
                    "properties": json.loads(r[4]) if r[4] else {},
                    "confidence": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


# Singleton
_resolver = None

def get_entity_resolver() -> EntityResolver:
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver()
    return _resolver


if __name__ == "__main__":
    resolver = EntityResolver()
    
    print("=== Entity Resolution Test ===")
    
    # Register entities
    eid1 = resolver.register_entity("Sen", "person", {"role": "user"})
    eid2 = resolver.register_entity("sen", "person")  # Should merge with above
    eid3 = resolver.register_entity("Pak Budi", "person", {"role": "mentor"})
    
    print(f"Sen ID: {eid1}")
    print(f"sen ID: {eid2} (should match Sen)")
    print(f"Pak Budi ID: {eid3}")
    
    # Resolve
    result = resolver.resolve("Sen")
    print(f"Resolve 'Sen': {result['canonical_name'] if result else 'Not found'}")
    
    result = resolver.resolve("sen")
    print(f"Resolve 'sen': {result['canonical_name'] if result else 'Not found'}")
    
    # All entities
    entities = resolver.get_all_entities()
    print(f"Total canonical entities: {len(entities)}")
    for e in entities:
        print(f"  {e['canonical_name']} ({e['entity_type']}): {len(e['aliases'])} aliases")
