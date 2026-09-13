#!/usr/bin/env python3
"""
V42.0 — Model Router.
Tiered model selection for cost optimization.
"""

from typing import Dict, Optional
from enum import Enum

class TaskClass(Enum):
    SIMPLE = "simple"       # Classification, extraction, formatting
    STANDARD = "standard"   # General chat, Q&A
    COMPLEX = "complex"     # Reasoning, analysis, code generation
    PREMIUM = "premium"     # Complex multi-step reasoning

# Model routing configuration
MODEL_ROUTES: Dict[TaskClass, Dict] = {
    TaskClass.SIMPLE: {
        "models": ["gpt-4o-mini", "claude-3-haiku"],
        "max_tokens": 1000,
        "cost_per_1k": 0.0005,
    },
    TaskClass.STANDARD: {
        "models": ["gpt-4o", "claude-3-sonnet"],
        "max_tokens": 2000,
        "cost_per_1k": 0.003,
    },
    TaskClass.COMPLEX: {
        "models": ["gpt-4o", "claude-3-opus"],
        "max_tokens": 4000,
        "cost_per_1k": 0.01,
    },
    TaskClass.PREMIUM: {
        "models": ["gpt-4-turbo", "claude-3.5-sonnet"],
        "max_tokens": 8000,
        "cost_per_1k": 0.03,
    },
}

def classify_task(text: str) -> TaskClass:
    """Classify task complexity."""
    text_lower = text.lower()
    
    # Premium indicators
    if any(w in text_lower for w in ["analyze", "research", "architect", "design", "strategy"]):
        return TaskClass.PREMIUM
    
    # Complex indicators
    if any(w in text_lower for w in ["code", "debug", "implement", "function", "algorithm"]):
        return TaskClass.COMPLEX
    
    # Simple indicators
    if any(w in text_lower for w in ["what", "list", "define", "summarize", "classify"]):
        return TaskClass.SIMPLE
    
    return TaskClass.STANDARD

def get_model_for_task(text: str, current_model: str = None) -> Dict:
    """Get the best model for a task."""
    task_class = classify_task(text)
    route = MODEL_ROUTES[task_class]
    
    return {
        "models": route["models"],
        "max_tokens": route["max_tokens"],
        "cost_per_1k": route["cost_per_1k"],
        "task_class": task_class.value,
    }

router = get_model_for_task
