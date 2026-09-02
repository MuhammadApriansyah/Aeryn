"""Agent Loop — core agent cycle: LLM → Tool → Response.

Integrated with:
- Memory Recall: retrieve relevant memories before LLM call
- Memory Write: auto-save facts after conversation
- Context Window: token-bounded conversation history
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from aeryn_core.utils.llm_client import AerynLLMClient
from aeryn_core.tools import get_tool_registry
from aeryn_core.memory.recall import get_memory_recall
from aeryn_core.memory.write import get_memory_write
from aeryn_core.memory.context import ContextWindow, TokenCounter


class AgentLoop:
    """Core agent loop: system prompt → user message → LLM → tool calls → response."""
    
    def __init__(self, system_prompt: str = None, max_iterations: int = 10, max_tokens: int = 4000):
        self.llm = AerynLLMClient()
        self.tools = get_tool_registry()
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.recall = get_memory_recall()
        self.write = get_memory_write()
        self.context = ContextWindow(max_tokens=max_tokens)
        from aeryn_core.agent.divisions import get_division_manager
        self.divisions = get_division_manager()
    
    def _default_system_prompt(self) -> str:
        """Build default system prompt."""
        return f"""You are Aeryn, an AI assistant running in standalone mode.

You have access to tools. Use them when needed.

Rules:
- Think step by step
- Use tools when you need to execute commands, read/write files, or search
- Be concise and direct
- When you have a final answer, just respond normally (no tool call)

Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    async def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Run agent loop for a user message."""
        from aeryn_core.utils.llm_client import get_mode_router
        router = get_mode_router()
        session = router.get_or_create_session(session_id)
        
        # === DIVISION ROUTING: classify message ===
        division_id = self.divisions.classify(user_message)
        division_prompt = self.divisions.get_system_prompt(division_id)
        
        # === MEMORY RECALL: Get relevant memories ===
        relevant_memories = self.recall.recall(user_message, limit=3)
        memory_context = self.recall.format_for_prompt(relevant_memories)
        
        # Build system prompt with division + memory
        system_content = division_prompt
        if memory_context:
            system_content += "\n\n" + memory_context
        
        # Load history from session
        messages = [{"role": "system", "content": system_content}]
        messages.extend(session.messages)
        messages.append({"role": "user", "content": user_message})
        
        # === CONTEXT WINDOW: Trim if needed ===
        messages = self._trim_context(messages)
        
        tools_schema = self.tools.get_schemas()
        last_content = ""
        
        for iteration in range(self.max_iterations):
            # Get LLM response
            response = await self.llm.chat(
                messages=messages,
                session_id=session_id,
                tools=tools_schema
            )
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            last_content = content
            
            # Add to session
            session.add_message("user", user_message)
            
            if not tool_calls:
                session.add_message("assistant", content)
                
                # === MEMORY WRITE: Save facts after conversation ===
                self._save_facts(session_id, user_message, content, messages)
                
                return {
                    "role": "assistant",
                    "content": content,
                    "reasoning": response.get("reasoning", []),
                    "provider": response.get("provider", ""),
                    "model": response.get("model", ""),
                    "iterations": iteration + 1,
                    "memories_used": len(relevant_memories),
                    "division": division_id,
                }
            
            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            
            for tc in tool_calls:
                tool_name = tc.get("function", {}).get("name", "")
                tool_args = tc.get("function", {}).get("arguments", {})
                
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}
                
                result = await self.tools.call(tool_name, tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps(result),
                })
        
        # === MEMORY WRITE: Save even if max iterations ===
        self._save_facts(session_id, user_message, last_content, messages)
        
        return {
            "role": "assistant",
            "content": last_content + "\n\n(Max iterations reached)",
            "reasoning": [],
            "iterations": self.max_iterations,
            "memories_used": len(relevant_memories),
        }
    
    def _trim_context(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim messages to fit within token budget."""
        total_tokens = TokenCounter.count_messages(messages)
        
        if total_tokens <= self.max_tokens:
            return messages
        
        # Keep system prompt and recent messages
        system = [m for m in messages if m.get("role") == "system"]
        other = [m for m in messages if m.get("role") != "system"]
        
        # Keep last N messages that fit
        trimmed = []
        current_tokens = TokenCounter.count_messages(system)
        
        for msg in reversed(other):
            msg_tokens = TokenCounter.count_messages([msg])
            if current_tokens + msg_tokens > self.max_tokens:
                break
            trimmed.insert(0, msg)
            current_tokens += msg_tokens
        
        return system + trimmed
    
    def _save_facts(self, session_id: str, user_message: str, assistant_response: str, messages: List[Dict[str, Any]]):
        """Save facts from conversation."""
        try:
            # Extract facts from assistant response
            facts = self.write.extract_facts(assistant_response)
            for fact in facts:
                self.write.save_fact(fact.get("text", ""), source="conversation")
            
            # Save conversation summary
            self.write.save_conversation_summary(session_id, messages)
        except:
            pass
    
    async def run_stream(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Run agent loop with streaming response."""
        from aeryn_core.utils.llm_client import get_mode_router
        router = get_mode_router()
        session = router.get_or_create_session(session_id)
        
        # === MEMORY RECALL ===
        relevant_memories = self.recall.recall(user_message, limit=3)
        memory_context = self.recall.format_for_prompt(relevant_memories)
        
        system_content = self.system_prompt
        if memory_context:
            system_content += "\n\n" + memory_context
        
        messages = [{"role": "system", "content": system_content}]
        messages.extend(session.messages)
        messages.append({"role": "user", "content": user_message})
        
        messages = self._trim_context(messages)
        
        tools_schema = self.tools.get_schemas()
        
        for iteration in range(self.max_iterations):
            response = await self.llm.chat(
                messages=messages,
                session_id=session_id,
                tools=tools_schema
            )
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            
            if not tool_calls:
                session.add_message("user", user_message)
                session.add_message("assistant", content)
                
                # Save facts
                self._save_facts(session_id, user_message, content, messages)
                
                yield json.dumps({"type": "message", "content": content, "memories_used": len(relevant_memories)})
                return
            
            yield json.dumps({"type": "tool_calls", "tool_calls": tool_calls})
            
            messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            
            for tc in tool_calls:
                tool_name = tc.get("function", {}).get("name", "")
                tool_args = tc.get("function", {}).get("arguments", {})
                
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}
                
                yield json.dumps({"type": "tool_call", "tool": tool_name, "args": tool_args})
                
                result = await self.tools.call(tool_name, tool_args)
                
                yield json.dumps({"type": "tool_result", "tool": tool_name, "result": result})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps(result),
                })
        
        yield json.dumps({"type": "done", "reason": "max_iterations"})
