#!/usr/bin/env python3
"""V41.0 — Phase 2: Context Window Management + ReAct Loop."""

import os, json, asyncio
from typing import Dict, List, Optional
from datetime import datetime


class ContextWindowManager:
    """Manage LLM context window with summarization."""
    
    def __init__(self, max_tokens: int = 8000, summary_threshold: int = 6000):
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)."""
        return len(text) // 4
    
    def trim_messages(self, messages: List[Dict]) -> List[Dict]:
        """Trim messages to fit context window."""
        total_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Keep system message, trim from oldest
        result = []
        if messages and messages[0].get("role") == "system":
            result.append(messages[0])
            messages = messages[1:]
        
        # Add messages from newest until we hit the limit
        current_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in result)
        
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if current_tokens + msg_tokens > self.max_tokens * 0.8:
                break
            result.insert(1, msg)  # Insert after system
            current_tokens += msg_tokens
        
        return result
    
    def should_summarize(self, messages: List[Dict]) -> bool:
        """Check if messages should be summarized."""
        total_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)
        return total_tokens > self.summary_threshold


class ReActLoop:
    """ReAct (Reasoning + Acting) loop for complex tasks."""
    
    def __init__(self, llm_client, tool_runtime):
        self.llm = llm_client
        self.tools = tool_runtime
        self.max_iterations = 10
    
    async def run(self, user_message: str, session_id: str = "default") -> Dict:
        """Execute ReAct loop."""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": user_message},
        ]
        
        for i in range(self.max_iterations):
            # Think
            result = await self.llm.chat(messages)
            response = result.get("content", "")
            
            # Check if final answer
            if self._is_final_answer(response):
                return {"answer": response, "iterations": i + 1}
            
            # Parse action
            action = self._parse_action(response)
            if not action:
                return {"answer": response, "iterations": i + 1}
            
            # Execute action
            tool_result = await self.tools.execute(action["tool"], action.get("params", {}))
            
            # Add observation
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Observation: {tool_result.to_dict()}"})
        
        return {"answer": "Max iterations reached", "iterations": self.max_iterations}
    
    def _get_system_prompt(self) -> str:
        return """You are Aeryn, a cognitive agent. Use ReAct (Reasoning + Acting) to solve tasks.

Format:
Thought: Your reasoning about what to do
Action: tool_name with parameters
Observation: Result of the action
... (repeat until done)
Final Answer: Your final response

Available tools: terminal, fs_read, fs_write, web_search, web_fetch, python"""
    
    def _is_final_answer(self, response: str) -> bool:
        return "Final Answer:" in response or "final answer:" in response.lower()
    
    def _parse_action(self, response: str) -> Optional[Dict]:
        """Parse action from response."""
        import re
        match = re.search(r"Action:\s*(\w+)\s*(.*)", response)
        if match:
            return {
                "tool": match.group(1),
                "params": {"query": match.group(2).strip()},
            }
        return None


# ── Singletons ────────────────────────────────

_context_manager: Optional[ContextWindowManager] = None

def get_context_manager() -> ContextWindowManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextWindowManager()
    return _context_manager
