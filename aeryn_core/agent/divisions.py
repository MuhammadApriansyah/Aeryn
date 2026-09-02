"""Division Manager — route requests to correct cognitive division.

5 divisions:
- creative: style, POV, narrative
- psych: mental health, peace
- reasoning: MCTS, FOL, critique, graph
- gov: constitutional compliance, requirements
- infra: sync, validation, consensus
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class Division:
    """Represents a cognitive division."""
    id: str
    name: str
    description: str
    system_prompt: str
    keywords: List[str]


# Division definitions
DIVISIONS = {
    "creative": Division(
        id="creative",
        name="Creative Division",
        description="Style, POV, narrative, prose",
        system_prompt="""You are the Creative Division of Aeryn, focused on narrative craft, style, and point-of-view.

Your strengths:
- Deep point-of-view enforcement
- Lexical style switching
- Narrative rhythm and pacing
- Vivid sensory detail

Approach every task with attention to voice, tone, and craft.""",
        keywords=["write", "story", "narrative", "prose", "style", "creative", "poem", "novel", "character", "plot", "pov", "fiction", "dialogue", "scene"],
    ),
    "psych": Division(
        id="psych",
        name="Psychological Division",
        description="Mental health, peace, well-being",
        system_prompt="""You are the Psychological Division of Aeryn, focused on mental well-being and emotional peace.

Your strengths:
- Emotional intelligence
- Empathetic communication
- Mental health awareness
- Peace-building

Approach every task with compassion and emotional attunement.""",
        keywords=["feel", "emotion", "anxiety", "stress", "depress", "sad", "angry", "lonely", "peace", "calm", "mental", "health", "therapy", "support", "worry"],
    ),
    "reasoning": Division(
        id="reasoning",
        name="Neuro-Symbolic Reasoning Division",
        description="MCTS, FOL, critique, graph",
        system_prompt="""You are the Reasoning Division of Aeryn, focused on rigorous logical analysis.

Your strengths:
- Monte Carlo Tree Search planning
- First-order logic predicates
- Critical critique
- Epistemic graph traversal

Approach every task with structured reasoning and evidence-based analysis.""",
        keywords=["analyze", "logic", "reason", "solve", "why", "how", "compare", "evaluate", "proof", "predict", "calculate", "debate", "critique", "plan", "strategy"],
    ),
    "gov": Division(
        id="gov",
        name="Sovereign Governance Division",
        description="Constitutional compliance, requirements",
        system_prompt="""You are the Governance Division of Aeryn, focused on compliance and requirements.

Your strengths:
- Context drift detection
- EARS requirements parsing
- Constitutional compliance
- Policy enforcement

Approach every task with attention to rules, requirements, and correctness.""",
        keywords=["requirement", "compliance", "rule", "policy", "spec", "standard", "audit", "review", "check", "verify", "constraint", "contract"],
    ),
    "infra": Division(
        id="infra",
        name="Infrastructure Division",
        description="Sync, validation, consensus",
        system_prompt="""You are the Infrastructure Division of Aeryn, focused on system reliability.

Your strengths:
- Narrative ledger sync
- Transaction validation
- Consensus building
- System integration

Approach every task with attention to consistency and reliability.""",
        keywords=["sync", "deploy", "server", "database", "api", "integration", "consensus", "validate", "system", "infra", "config", "setup", "install"],
    ),
}


class DivisionManager:
    """Route requests to correct cognitive division."""
    
    def __init__(self):
        self.divisions = DIVISIONS
    
    def classify(self, message: str) -> str:
        """Classify message into a division by keyword matching."""
        message_lower = message.lower()
        scored = {}
        
        for div_id, div in self.divisions.items():
            score = sum(1 for kw in div.keywords if kw in message_lower)
            scored[div_id] = score
        
        # Find division with highest score
        best_id = max(scored, key=lambda k: scored[k])
        
        # If no keywords matched, default to reasoning
        if scored[best_id] == 0:
            return "reasoning"
        
        return best_id
    
    def get_division(self, div_id: str) -> Optional[Division]:
        """Get division by id."""
        return self.divisions.get(div_id)
    
    def get_system_prompt(self, div_id: str) -> str:
        """Get system prompt for a division."""
        div = self.divisions.get(div_id)
        if div:
            return div.system_prompt
        return DIVISIONS["reasoning"].system_prompt
    
    def list_divisions(self) -> List[Dict[str, Any]]:
        """List all divisions."""
        return [
            {"id": d.id, "name": d.name, "description": d.description}
            for d in self.divisions.values()
        ]


# Global instance
_manager = None

def get_division_manager() -> DivisionManager:
    """Get global division manager."""
    global _manager
    if _manager is None:
        _manager = DivisionManager()
    return _manager