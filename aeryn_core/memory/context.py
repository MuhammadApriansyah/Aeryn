"""Context Window — token-bounded conversation history."""

import json
from typing import List, Dict, Any, Optional


class ContextWindow:
    """Manage conversation within token limits."""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to context."""
        self.messages.append({"role": role, "content": content})
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)."""
        return len(text) // 4
    
    def get_context(self) -> List[Dict[str, str]]:
        """Get messages that fit within token budget."""
        context = []
        total_tokens = 0
        
        # Always include system prompt first
        system_msg = None
        other_messages = []
        
        for msg in self.messages:
            if msg.get("role") == "system":
                system_msg = msg
            else:
                other_messages.append(msg)
        
        if system_msg:
            context.append(system_msg)
            total_tokens += self.estimate_tokens(system_msg.get("content", ""))
        
        # Add recent messages (newest first)
        for msg in reversed(other_messages):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if total_tokens + msg_tokens > self.max_tokens:
                break
            context.insert(1, msg)  # Insert after system
            total_tokens += msg_tokens
        
        return context
    
    def should_summarize(self) -> bool:
        """Check if context should be summarized."""
        total_tokens = sum(
            self.estimate_tokens(msg.get("content", ""))
            for msg in self.messages
        )
        return total_tokens > self.max_tokens * 0.8
    
    def summarize_old_messages(self) -> str:
        """Summarize old messages to save tokens."""
        old_messages = self.messages[1:-5]  # Exclude system and recent
        if not old_messages:
            return ""
        
        summary = "Previous conversation summary:\n"
        for msg in old_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            summary += f"- {role}: {content}\n"
        
        # Replace old messages with summary
        self.messages = [self.messages[0]] + old_messages[-5:]
        
        return summary


class TokenCounter:
    """Count tokens for context management."""
    
    @staticmethod
    def count(text: str) -> int:
        """Count tokens in text."""
        return len(text) // 4
    
    @staticmethod
    def count_messages(messages: List[Dict[str, str]]) -> int:
        """Count total tokens in messages."""
        return sum(len(msg.get("content", "")) // 4 for msg in messages)
    
    @staticmethod
    def truncate(text: str, max_tokens: int) -> str:
        """Truncate text to max tokens."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
