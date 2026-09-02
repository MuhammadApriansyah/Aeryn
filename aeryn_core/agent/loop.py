"""Agent Loop — core agent cycle: LLM → Tool → Response."""

import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from aeryn_core.utils.llm_client import AerynLLMClient
from aeryn_core.tools import get_tool_registry


class AgentLoop:
    """Core agent loop: system prompt → user message → LLM → tool calls → response."""
    
    def __init__(self, system_prompt: str = None, max_iterations: int = 10):
        self.llm = AerynLLMClient()
        self.tools = get_tool_registry()
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt or self._default_system_prompt()
    
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
        
        # Load history from session
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(session.messages)
        messages.append({"role": "user", "content": user_message})
        
        tools_schema = self.tools.get_schemas()
        last_content = ""
        
        for iteration in range(self.max_iterations):
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
                return {
                    "role": "assistant",
                    "content": content,
                    "reasoning": response.get("reasoning", []),
                    "provider": response.get("provider", ""),
                    "model": response.get("model", ""),
                    "iterations": iteration + 1,
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
        
        return {
            "role": "assistant",
            "content": last_content + "\n\n(Max iterations reached)",
            "reasoning": [],
            "iterations": self.max_iterations,
        }
    
    async def run_stream(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Run agent loop with streaming response."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        
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
                yield json.dumps({"type": "message", "content": content})
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
