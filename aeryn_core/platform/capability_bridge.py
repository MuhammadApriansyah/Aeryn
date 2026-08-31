#!/usr/bin/env python3
"""V61.0 — Capability Bridge: transfers Hermes-style dynamic skills + memory tiering to Aeryn.

Loads skills from aeryn_core/skills/ directory on demand and provides semantic
memory recall for chat context enrichment. Real implementations, no stubs.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


class SkillLoader:
    """Dynamic skill loader — mirrors Hermes skill loading behavior."""

    def __init__(self):
        self._skills: Dict[str, Dict] = {}
        self._loaded = False

    def load_all(self):
        """Scan skills/ directory and load metadata."""
        if self._loaded:
            return self._skills
        logger.info(f"SkillLoader: scanning {SKILLS_DIR}")
        if not os.path.isdir(SKILLS_DIR):
            logger.warning(f"Skills dir not found: {SKILLS_DIR}")
            self._loaded = True
            return {}
        for name in os.listdir(SKILLS_DIR):
            skill_path = os.path.join(SKILLS_DIR, name)
            if os.path.isdir(skill_path):
                manifest = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(manifest):
                    try:
                        with open(manifest, encoding="utf-8") as f:
                            content = f.read()
                        # Parse frontmatter (simple --- delimited)
                        desc = ""
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                fm = parts[1]
                                for line in fm.splitlines():
                                    if line.lower().startswith("description:"):
                                        desc = line.split(":", 1)[1].strip()
                        self._skills[name] = {
                            "name": name,
                            "path": skill_path,
                            "description": desc[:200],
                            "manifest": manifest,
                        }
                    except Exception as e:
                        logger.error(f"Failed to load skill {name}: {e}")
        self._loaded = True
        logger.info(f"Loaded {len(self._skills)} skills")
        return self._skills

    def get_skill(self, name: str) -> Optional[Dict]:
        self.load_all()
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        self.load_all()
        return list(self._skills.keys())


class FallbackRecall:
    """Fallback memory recall using vault search when episodes.jsonl unavailable."""
    
    def __init__(self):
        from aeryn_core.memory.vault import AerynVault
        self.vault = AerynVault()
    
    def recall(self, goal: str, k: int = 3) -> list:
        """Search vault for relevant entries."""
        try:
            results = self.vault.search(goal, limit=k)
            return [{"source": "vault", "path": r.get("path", ""), "preview": r.get("preview", "")} for r in results]
        except Exception:
            return []


class MemoryTierBridge:
    """Bridges semantic_recall + memory_indexer to chat context."""

    def __init__(self):
        self._recall = None

    def _get_recall(self):
        if self._recall is None:
            try:
                from aeryn_core.memory.semantic_recall import SemanticRecall
                episode_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "Personalisasi", "Database", "episodes.jsonl"
                )
                # Fallback: if episodes.jsonl doesn't exist, use vault search
                if not os.path.exists(episode_path):
                    from aeryn_core.memory.vault import AerynVault
                    self._recall = FallbackRecall()
                else:
                    self._recall = SemanticRecall(episode_path)
            except Exception as e:
                logger.warning(f"SemanticRecall unavailable: {e}")
                self._recall = FallbackRecall()
        return self._recall

    def recall_context(self, goal: str, k: int = 3) -> List[Dict]:
        """Return top-k relevant memories for chat context."""
        recall = self._get_recall()
        if recall is False:
            return []
        try:
            return recall.recall(goal, k=k)
        except Exception as e:
            logger.error(f"Memory recall failed: {e}")
            return []


# Singletons
_skill_loader = None
_memory_bridge = None

def get_skill_loader() -> SkillLoader:
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader

def get_memory_bridge() -> MemoryTierBridge:
    global _memory_bridge
    if _memory_bridge is None:
        _memory_bridge = MemoryTierBridge()
    return _memory_bridge
