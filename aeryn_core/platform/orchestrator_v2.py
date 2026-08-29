"""V39.38 — Simplified Cognitive Orchestrator: 5 divisions → 3 modules.

Modules:
  1. Reasoning  — prompt compilation, tool selection, plan execution
  2. Memory     — social memory, vault/graph, emotional state
  3. Governance — safety, rate limiting, constitutional compliance

Removed: mock state, dead code, unused divisions (creative/style/MCTS/FOL).
"""

import json
import time
import threading
from collections import defaultdict, deque
from typing import Optional, Dict, List

from aeryn_core.safety.safety_engine import (
    SafetyEngine, get_safety_engine, RateLimiter,
    validate_run_payload, sanitize_goal_for_sop,
    check_path, looks_like_injection, wrap_untrusted,
    get_guardian, sanitize_output, rotate_all_data_files,
)
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI, ensure_dirs
from aeryn_core.memory.graph import VaultGraph
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.utils.persona_engine import load_persona, PersonaEngine


class ReasoningModule:
    """Handles prompt compilation, tool selection, and plan execution."""
    
    def __init__(self):
        self.persona = PersonaEngine()
    
    def compile_system_prompt(self, goal: str, session_id: str, 
                              context: dict = None) -> str:
        """Compile full system prompt for the LLM."""
        parts = []
        
        # 1. Base persona
        parts.append(self.persona.get())
        
        # 2. CoT rule
        from aeryn_core.reasoning.reasoning_style import COGNITIVE_CHAIN_OF_THOUGHT_RULE
        parts.append(COGNITIVE_CHAIN_OF_THOUGHT_RULE)
        
        # 3. Research-first rule (if needed)
        if needs_research(goal):
            from aeryn_core.reasoning.reasoning_style import RESEARCH_FIRST_RULE
            parts.append(RESEARCH_FIRST_RULE)
        
        # 4. Adapter behavior contract
        adapter_ctx = render_adapter_context(goal)
        if adapter_ctx:
            parts.append(adapter_ctx)
        
        # 5. Cerewet mode (commitment tracking)
        from aeryn_core.reasoning.cerewet_mode import cerewet_context_block, CEREWET_RULES
        cerewet_block = cerewet_context_block(session_id)
        if cerewet_block:
            parts.append(CEREWET_RULES)
            parts.append(cerewet_block)
        
        # 6. Vault state (if graph context available)
        try:
            vault = AerynVault()
            graph = VaultGraph(vault=vault)
            summary = graph.render_graph_summary(goal)
            if summary and "0 nodes" not in summary:
                parts.append(f"\n{summary}")
        except Exception:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass
        
        # 7. External context (from Hermes reflex)
        if context and context.get("hermes_reflex"):
            parts.append(context["hermes_reflex"])
        
        return "\n\n".join(parts)
    
    def select_tools(self, goal: str, available_tools: list) -> list:
        """Select relevant tools for the goal."""
        from aeryn_core.utils.dynamic_schema import build_dynamic_schemas
        return build_dynamic_schemas(available_tools, goal)
    
    def build_next_token_hint(self, session_id: str) -> str:
        """Build a short hint for continuity."""
        from aeryn_core.reasoning.reasoning_style import build_next_token_hint
        return build_next_token_hint()


class MemoryModule:
    """Handles social memory, vault/graph, and emotional state."""
    
    def __init__(self):
        self.social = SocialMemory()
        ensure_dirs()
        self.vault = AerynVault()
        self._emotional_state = {}
        self._state_lock = threading.Lock()
    
    def get_social_context(self, user_id: str) -> str:
        """Get social memory context for a user."""
        person = self.social.touch_person(user_id, "")
        if not person:
            return ""
        
        facts = self.social.get_facts(user_id)
        if not facts:
            return ""
        
        block = "## KONTEKS USER TERDAFTAR\n"
        block += f"Orang ini sudah pernah interaksi sebelumnya.\n"
        block += f"Fakta terakhir: {', '.join(facts[-5:])}\n"
        return block
    
    def record_interaction(self, user_id: str, role: str, content: str):
        """Record interaction turn."""
        if role == "user":
            # Extract commitments
            from aeryn_core.reasoning.cerewet_mode import detect_commitment, add_commitment
            commitment = detect_commitment(content)
            if commitment:
                add_commitment(user_id, commitment)
            
            # Record fact
            self.social.add_fact(user_id, content[:200])
    
    def update_emotional_state(self, session_id: str, state: dict):
        """Update emotional state for a session."""
        with self._state_lock:
            self._emotional_state[session_id] = {
                **state,
                "updated_at": time.time()
            }
    
    def get_emotional_state(self, session_id: str) -> dict:
        """Get emotional state for a session."""
        with self._state_lock:
            return self._emotional_state.get(session_id, {})
    
    def render_graph_context(self, query: str) -> str:
        """Render graph context for a query."""
        try:
            graph = VaultGraph(vault=self.vault)
            return graph.render_graph_summary(query)
        except Exception:
            return ""


class GovernanceModule:
    """Handles safety, rate limiting, and constitutional compliance."""
    
    def __init__(self):
        self.safety = get_safety_engine()
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
    
    def validate_input(self, goal: str, session_id: str) -> tuple:
        """Validate input: payload + safety. Returns (ok, reason)."""
        # Payload validation
        ok, reason = validate_run_payload(goal, session_id)
        if not ok:
            return False, reason
        
        # Rate limit
        if not self.rate_limiter.allow(session_id):
            return False, "rate limit exceeded — coba lagi nanti"
        
        # Safety check on RAW goal first (before sanitization strips injection markers)
        result = self.safety.check_input(goal)
        if not result.safe:
            if result.fallback:
                return False, result.fallback
            return False, f"permintaan ditolak: {result.reason}"
        
        return True, ""
    
    def validate_output(self, text: str) -> tuple:
        """Validate output: sanitize if needed. Returns (cleaned_text, was_sanitized)."""
        result = self.safety.check_output(text)
        if not result.safe:
            return self.sanitize(text), True
        return text, False
    
    def sanitize(self, text: str) -> str:
        """Sanitize output."""
        return sanitize_output(text)
    
    def check_path(self, path: str, mode: str = "read", roots=None):
        """Validate file path."""
        return check_path(path, mode, roots)


class CognitiveOrchestrator:
    """Unified orchestrator: Reasoning + Memory + Governance."""
    
    def __init__(self):
        self.reasoning = ReasoningModule()
        self.memory = MemoryModule()
        self.governance = GovernanceModule()
    
    def compile_prompt(self, goal: str, session_id: str, 
                       context: dict = None) -> str:
        """Compile complete system prompt."""
        return self.reasoning.compile_system_prompt(goal, session_id, context)
    
    def validate_and_sanitize(self, goal: str, session_id: str) -> tuple:
        """Validate input goal. Returns (ok, reason_or_clean_goal)."""
        ok, reason = self.governance.validate_input(goal, session_id)
        if not ok:
            return False, reason
        # Don't re-sanitize — safety already checked raw goal
        return True, goal
    
    def process_output(self, text: str) -> tuple:
        """Process output: validate + sanitize."""
        return self.governance.validate_output(text)
    
    def record_turn(self, user_id: str, role: str, content: str):
        """Record a turn in memory."""
        self.memory.record_interaction(user_id, role, content)
    
    def get_user_context(self, user_id: str) -> str:
        """Get user context from social memory."""
        return self.memory.get_social_context(user_id)


# Singleton
_orchestrator = None

def get_orchestrator() -> CognitiveOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CognitiveOrchestrator()
    return _orchestrator
