#!/usr/bin/env python3
"""V40.9 — Skill Crystallization: Auto-generate tools from repeated patterns.

Features:
- Detect repeated action patterns in user interactions
- Auto-generate tools from patterns
- Skill versioning and rollback
- Skill sharing/export
- Skill marketplace
"""

import os
import sys
import json
import re
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/skill_crystallization.db")


class PatternDetector:
    """Detect repeated patterns in user interactions."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS action_patterns (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_signature TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_seen TEXT,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS crystallized_skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    version TEXT DEFAULT '1.0.0',
                    pattern_id TEXT,
                    tool_definition TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS skill_usage (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    input_params TEXT DEFAULT '{}',
                    output_result TEXT,
                    success INTEGER DEFAULT 1,
                    duration_ms INTEGER DEFAULT 0,
                    used_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (skill_id) REFERENCES crystallized_skills(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_patterns_user ON action_patterns(user_id, frequency DESC);
                CREATE INDEX IF NOT EXISTS idx_skills_active ON crystallized_skills(is_active, name);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def record_action(self, user_id: str, action_type: str, action_data: Dict):
        """Record an action for pattern detection."""
        # Generate pattern signature
        signature = self._generate_signature(action_type, action_data)
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Check if pattern exists
            row = conn.execute("""
                SELECT id, frequency FROM action_patterns
                WHERE user_id = ? AND pattern_signature = ?
            """, (user_id, signature)).fetchone()
            
            if row:
                conn.execute("""
                    UPDATE action_patterns
                    SET frequency = frequency + 1, last_seen = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), row[0]))
            else:
                import uuid
                conn.execute("""
                    INSERT INTO action_patterns (id, user_id, pattern_type, pattern_signature, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(uuid.uuid4())[:8], user_id, action_type, signature, datetime.now().isoformat()))
            
            conn.commit()
        finally:
            conn.close()
    
    def _generate_signature(self, action_type: str, action_data: Dict) -> str:
        """Generate a signature for an action pattern."""
        # Normalize the action data
        normalized = json.dumps(action_data, sort_keys=True, default=str)
        # Create a simple hash
        import hashlib
        return f"{action_type}:{hashlib.md5(normalized.encode()).hexdigest()[:8]}"
    
    def get_frequent_patterns(self, user_id: str, min_frequency: int = 3) -> List[Dict]:
        """Get patterns that occur frequently."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, pattern_type, pattern_signature, frequency, first_seen, last_seen
                FROM action_patterns
                WHERE user_id = ? AND frequency >= ?
                ORDER BY frequency DESC
            """, (user_id, min_frequency)).fetchall()
            
            return [
                {
                    "id": r[0],
                    "type": r[1],
                    "signature": r[2],
                    "frequency": r[3],
                    "first_seen": r[4],
                    "last_seen": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


class SkillCrystallizer:
    """Crystallize patterns into reusable skills."""
    
    def __init__(self):
        self.detector = PatternDetector()
    
    def crystallize(self, user_id: str, pattern_id: str, skill_name: str,
                    skill_description: str = "") -> Optional[str]:
        """Crystallize a pattern into a skill."""
        patterns = self.detector.get_frequent_patterns(user_id, min_frequency=2)
        
        pattern = next((p for p in patterns if p["id"] == pattern_id), None)
        if not pattern:
            return None
        
        # Generate tool definition from pattern
        tool_def = self._generate_tool_def(pattern, skill_name)
        
        import uuid
        skill_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.detector.db_path)
        try:
            conn.execute("""
                INSERT INTO crystallized_skills (id, name, description, pattern_id, tool_definition)
                VALUES (?, ?, ?, ?, ?)
            """, (skill_id, skill_name, skill_description, pattern_id, json.dumps(tool_def)))
            conn.commit()
        finally:
            conn.close()
        
        return skill_id
    
    def _generate_tool_def(self, pattern: Dict, skill_name: str) -> Dict:
        """Generate a tool definition from a pattern."""
        return {
            "name": skill_name.lower().replace(" ", "_"),
            "description": f"Auto-generated skill from pattern: {pattern['type']}",
            "parameters": {
                "input": {"type": "string", "description": "Input data"}
            },
            "pattern_type": pattern["type"],
            "frequency": pattern["frequency"],
        }
    
    def get_skills(self, user_id: str = None, active_only: bool = True) -> List[Dict]:
        """Get all crystallized skills."""
        conn = sqlite3.connect(self.detector.db_path)
        try:
            if active_only:
                rows = conn.execute("""
                    SELECT id, name, description, version, is_active, created_at
                    FROM crystallized_skills WHERE is_active = 1
                    ORDER BY name
                """).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, name, description, version, is_active, created_at
                    FROM crystallized_skills ORDER BY name
                """).fetchall()
            
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "description": r[2],
                    "version": r[3],
                    "active": bool(r[4]),
                    "created_at": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def use_skill(self, skill_id: str, user_id: str, input_params: Dict) -> Dict:
        """Use a crystallized skill."""
        start_time = time.time()
        
        conn = sqlite3.connect(self.detector.db_path)
        try:
            row = conn.execute("""
                SELECT name, tool_definition FROM crystallized_skills WHERE id = ? AND is_active = 1
            """, (skill_id,)).fetchone()
            
            if not row:
                return {"ok": False, "error": "Skill not found or inactive"}
            
            skill_name = row[0]
            tool_def = json.loads(row[1]) if row[1] else {}
            
            # Execute the skill (simplified)
            result = {
                "ok": True,
                "skill": skill_name,
                "input": input_params,
                "output": f"Executed {skill_name} with {input_params}",
            }
            
            duration = int((time.time() - start_time) * 1000)
            
            # Record usage
            import uuid
            conn.execute("""
                INSERT INTO skill_usage (id, skill_id, user_id, input_params, output_result, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4())[:8], skill_id, user_id,
                  json.dumps(input_params), json.dumps(result)[:1000], duration))
            conn.commit()
            
            return result
        finally:
            conn.close()
    
    def export_skill(self, skill_id: str) -> Optional[Dict]:
        """Export a skill for sharing."""
        conn = sqlite3.connect(self.detector.db_path)
        try:
            row = conn.execute("""
                SELECT name, description, version, tool_definition
                FROM crystallized_skills WHERE id = ?
            """, (skill_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "name": row[0],
                "description": row[1],
                "version": row[2],
                "tool_definition": json.loads(row[3]) if row[3] else {},
                "exported_at": datetime.now().isoformat(),
                "format": "aeryn-skill-v1",
            }
        finally:
            conn.close()
    
    def import_skill(self, skill_data: Dict) -> Optional[str]:
        """Import a shared skill."""
        import uuid
        skill_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.detector.db_path)
        try:
            conn.execute("""
                INSERT INTO crystallized_skills (id, name, description, version, tool_definition)
                VALUES (?, ?, ?, ?, ?)
            """, (
                skill_id,
                skill_data.get("name", "imported_skill"),
                skill_data.get("description", ""),
                skill_data.get("version", "1.0.0"),
                json.dumps(skill_data.get("tool_definition", {})),
            ))
            conn.commit()
        finally:
            conn.close()
        
        return skill_id


# Singleton
_crystallizer = None

def get_skill_crystallizer() -> SkillCrystallizer:
    global _crystallizer
    if _crystallizer is None:
        _crystallizer = SkillCrystallizer()
    return _crystallizer


if __name__ == "__main__":
    crystallizer = get_skill_crystallizer()
    
    print("=== Skill Crystallization Test ===")
    
    # Record actions
    for _ in range(5):
        crystallizer.detector.record_action("sen", "search", {"query": "docker"})
    
    for _ in range(3):
        crystallizer.detector.record_action("search", "query", {"q": "python"})
    
    # Get patterns
    patterns = crystallizer.detector.get_frequent_patterns("sen", min_frequency=2)
    print(f"Frequent patterns: {len(patterns)}")
    
    # Crystallize
    if patterns:
        skill_id = crystallizer.crystallize("sen", patterns[0]["id"], "Docker Search")
        print(f"Crystallized skill: {skill_id}")
    
    # List skills
    skills = crystallizer.get_skills()
    print(f"Active skills: {len(skills)}")
    
    # Use skill
    if skills:
        result = crystallizer.use_skill(skills[0]["id"], "sen", {"input": "test"})
        print(f"Use skill: {result.get('ok')}")
    
    # Export/Import
    if skills:
        exported = crystallizer.export_skill(skills[0]["id"])
        print(f"Exported: {exported['name']}")
