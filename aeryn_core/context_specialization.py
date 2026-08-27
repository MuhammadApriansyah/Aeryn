#!/usr/bin/env python3
"""V39.69 — Context Specialization: Dynamic context loading based on goal type.

Goal categories:
- personal → persona + social memory + facts
- technical → tools + debug adapter + vault
- research → research adapter + web tools
- creative → creative adapter
- simple → minimal context
"""

import os
import sys
import re
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.persona_engine import load_persona
from aeryn_core.social_memory import SocialMemory
from aeryn_core.adapters import render_adapter_context
from aeryn_core.vault import AerynVault, LAYER_WIKI
from aeryn_core.reasoning_style import needs_research


@dataclass
class ContextSpec:
    """Specialized context for a goal type."""
    name: str
    persona_truncate: int = 0  # 0 = full, >0 = truncate to N chars
    load_social: bool = False
    load_vault: bool = False
    load_tools: bool = False
    load_research: bool = False
    adapter_override: Optional[str] = None
    system_prefix: str = ""


# ── Goal Classifier ──────────────────────────────────────────────

class GoalClassifier:
    """Rule-based goal classification."""
    
    PATTERNS = {
        "personal": [
            r"\b(hai|halo|hi|hey|siapa|nama|kabar|apa kabar|gimana|how are you)\b",
            r"\b(suka|sayang|rindu|senang|sedih|marah|takut)\b",
            r"\b(aku|kamu|kitasama|kami)\b",
        ],
        "technical": [
            r"\b(install|pasang|setup|config|debug|error|bug|fix|deploy)\b",
            r"\b(docker|kubernetes|linux|python|node|react|vue|git|sql)\b",
            r"\b(code|programming|script|command|terminal|shell)\b",
        ],
        "research": [
            r"\b(riset|research|cari|search|gali|explore|investigate)\b",
            r"\b(apa itu|what is|jelaskan|explain|mengapa|why|how to)\b",
            r"\b(terbaru|latest|trend|perkembangan|development)\b",
        ],
        "creative": [
            r"\b(tulis|write|buat|create|cerita|story|puisi|poem)\b",
            r"\b(design|gambar|image|visual|layout|mockup)\b",
            r"\b(ide|ideas|inspirasi|brainstorm|concept)\b",
        ],
    }
    
    @classmethod
    def classify(cls, goal: str) -> str:
        """Classify goal into a category."""
        goal_lower = goal.lower()
        
        scores = {}
        for category, patterns in cls.PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, goal_lower))
            if score > 0:
                scores[category] = score
        
        if not scores:
            return "simple"
        
        return max(scores, key=lambda k: scores[k])


# ── Context Builder ──────────────────────────────────────────────

class ContextBuilder:
    """Build specialized context based on goal type."""
    
    def __init__(self):
        self.classifier = GoalClassifier()
        self.sm = SocialMemory()
        self.vault = AerynVault()
    
    def build(self, goal: str, session_id: str = "default") -> ContextSpec:
        """Build context spec for a goal."""
        category = self.classifier.classify(goal)
        
        if category == "personal":
            return self._build_personal(goal, session_id)
        elif category == "technical":
            return self._build_technical(goal, session_id)
        elif category == "research":
            return self._build_research(goal, session_id)
        elif category == "creative":
            return self._build_creative(goal, session_id)
        else:
            return self._build_simple(goal, session_id)
    
    def _build_personal(self, goal: str, session_id: str) -> ContextSpec:
        """Personal context: persona + social memory + facts."""
        facts = self.sm.get_facts(session_id)
        facts_text = ""
        if facts:
            facts_text = f"\n[Fakta tentang user: {', '.join(str(f) for f in facts[:5])}]"
        
        return ContextSpec(
            name="personal",
            persona_truncate=0,  # Full persona
            load_social=True,
            load_vault=False,
            load_tools=False,
            load_research=False,
            system_prefix=f"{facts_text}\nMode personal: hangat, empati, gunakan memori percakapan.",
        )
    
    def _build_technical(self, goal: str, session_id: str) -> ContextSpec:
        """Technical context: tools + debug adapter + vault search."""
        # Search vault for relevant technical info
        vault_context = ""
        try:
            results = self.vault.search(goal, layer=LAYER_WIKI, limit=3)
            if results:
                vault_context = "\n[Relevan dari vault:\n"
                for r in results:
                    vault_context += f"  - {r.get('preview', '')[:150]}\n"
                vault_context += "]"
        except Exception:
            pass
        
        return ContextSpec(
            name="technical",
            persona_truncate=200,  # Short persona
            load_social=False,
            load_vault=True,
            load_tools=True,
            load_research=False,
            system_prefix=f"{vault_context}\nMode teknis: fokus, detail, gunakan tools bila perlu.",
        )
    
    def _build_research(self, goal: str, session_id: str) -> ContextSpec:
        """Research context: research adapter + web tools."""
        return ContextSpec(
            name="research",
            persona_truncate=200,
            load_social=False,
            load_vault=False,
            load_tools=True,
            load_research=True,
            adapter_override="research",
            system_prefix="Mode riset: sistematis, verifikasi sumber, sebut referensi.",
        )
    
    def _build_creative(self, goal: str, session_id: str) -> ContextSpec:
        """Creative context: creative adapter."""
        return ContextSpec(
            name="creative",
            persona_truncate=0,  # Full persona for warmth
            load_social=False,
            load_vault=False,
            load_tools=False,
            load_research=False,
            adapter_override="explain",  # Use explain as creative base
            system_prefix="Mode kreatif: imajinatif, ekspresif, gunakan bahasa yang hidup.",
        )
    
    def _build_simple(self, goal: str, session_id: str) -> ContextSpec:
        """Simple context: minimal, fast."""
        return ContextSpec(
            name="simple",
            persona_truncate=100,  # Minimal persona
            load_social=False,
            load_vault=False,
            load_tools=False,
            load_research=False,
            system_prefix="",
        )
    
    def compile_prompt(self, goal: str, session_id: str = "default") -> Dict:
        """Compile full prompt with specialized context."""
        spec = self.build(goal, session_id)
        
        # Load persona (truncated if needed)
        persona = load_persona()
        if spec.persona_truncate > 0:
            persona = persona[:spec.persona_truncate] + "..."
        
        # Build system prompt
        parts = [persona]
        
        if spec.system_prefix:
            parts.append(f"\n{spec.system_prefix}")
        
        if spec.load_tools:
            parts.append("\nTools tersedia: web_search, web_read, fs_read, fs_write, terminal, memory_search")
        
        if spec.load_research:
            parts.append("\nMode riset aktif: pencarian web diperlukan untuk jawaban akurat.")
        
        if spec.adapter_override:
            adapter_ctx = render_adapter_context(goal)
            if adapter_ctx:
                parts.append(f"\n{adapter_ctx}")
        
        # Add social memory if personal
        if spec.load_social:
            facts = self.sm.get_facts(session_id)
            if facts:
                parts.append(f"\n[User: {', '.join(str(f) for f in facts[:3])}]")
        
        system_prompt = "\n".join(parts)
        
        return {
            "category": spec.name,
            "system_prompt": system_prompt,
            "goal": goal,
            "session_id": session_id,
            "prompt_length": len(system_prompt),
        }


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    builder = ContextBuilder()
    
    test_goals = [
        ("halo apa kabar", "user1"),
        ("install docker di ubuntu", "user1"),
        ("riset tentang AI terbaru 2024", "user1"),
        ("buat cerita pendek tentang robot", "user1"),
        ("2+2 berapa", "user1"),
        ("debug error SSL di nginx", "user2"),
    ]
    
    print("=== Context Specialization Test ===")
    for goal, session in test_goals:
        result = builder.compile_prompt(goal, session)
        print(f"\nGoal: {goal}")
        print(f"  Category: {result['category']}")
        print(f"  Prompt length: {result['prompt_length']} chars")
        print(f"  Preview: {result['system_prompt'][:120]}...")
