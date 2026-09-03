"""Agent Loop — core agent cycle: LLM → Tool → Response.

Integrated with:
- Memory Recall: retrieve relevant memories before LLM call
- Memory Write: auto-save facts after conversation
- Context Window: token-bounded conversation history
"""

import json
import asyncio
import time
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
    
    async def run(self, session_id: str, user_message: str, user_id: str = "default") -> Dict[str, Any]:
        """Run agent loop for a user message (user-scoped session)."""
        from aeryn_core.utils.llm_client import get_mode_router
        from aeryn_core.observability.tracing import (
            get_trace_collector, start_trace, ATTR_AGENT_NAME, ATTR_SESSION, ATTR_MODEL, ATTR_TOKENS_TOTAL, ATTR_TOOL_NAME
        )
        from aeryn_core.runtime.session_store import get_session_store
        router = get_mode_router()
        session = router.get_or_create_session(session_id)
        session_store = get_session_store()
        
        # === SESSION STATE: load persistent history (user-isolated) ===
        persisted = session_store.load_session(user_id, session_id)
        if persisted:
            history_messages = persisted.messages
        else:
            history_messages = []
        
        # === OBSERVABILITY: start trace + agent span ===
        collector = get_trace_collector()
        trace_id = start_trace(session_id)
        agent_span = collector.start_span(trace_id, None, "invoke_agent", {
            ATTR_AGENT_NAME: "aeryn",
            ATTR_SESSION: session_id,
        })
        t_start = time.time()
        
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
        
        # Load history from session (persistent + user-isolated)
        messages = [{"role": "system", "content": system_content}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": user_message})
        
        # === CONTEXT WINDOW: Trim if needed ===
        messages = self._trim_context(messages)
        
        tools_schema = self.tools.get_schemas()
        last_content = ""
        
        for iteration in range(self.max_iterations):
            # === OBSERVABILITY: LLM (chat) span ===
            chat_span = collector.start_span(trace_id, agent_span.id, "chat", {
                ATTR_SESSION: session_id,
            })
            c_start = time.time()
            
            # Get LLM response
            response = await self.llm.chat(
                messages=messages,
                session_id=session_id,
                tools=tools_schema
            )
            
            # End chat span with token + model attributes
            collector.end_span(chat_span, status="ok", attributes={
                ATTR_MODEL: response.get("model", "unknown"),
                ATTR_TOKENS_TOTAL: response.get("tokens", 0),
                "gen_ai.latency_ms": round((time.time() - c_start) * 1000, 2),
            })
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            last_content = content
            
            # Add to session
            session.add_message("user", user_message)
            
            if not tool_calls:
                session.add_message("assistant", content)
                
                # === MEMORY WRITE: Save facts after conversation ===
                self._save_facts(session_id, user_message, content, messages)
                
                # === SESSION STATE: persist history (user-isolated) ===
                persistent_history = history_messages + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": content},
                ]
                session_store.save_session(user_id, session_id, persistent_history)
                
                # End agent span
                collector.end_span(agent_span, status="ok", attributes={
                    "gen_ai.latency_ms": round((time.time() - t_start) * 1000, 2),
                    ATTR_AGENT_NAME: "aeryn",
                    "division": division_id,
                })
                
                return {
                    "role": "assistant",
                    "content": content,
                    "reasoning": response.get("reasoning", []),
                    "provider": response.get("provider", ""),
                    "model": response.get("model", ""),
                    "iterations": iteration + 1,
                    "memories_used": len(relevant_memories),
                    "division": division_id,
                    "trace_id": trace_id,
                    "user_id": user_id,
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
                
                # === GUARDRAIL: detect approval requirement ===
                pending_approval = self._precheck_approval(tool_name, tool_args)
                if pending_approval is not None:
                    # Surface approval request to human and STOP (HITL)
                    return {
                        "role": "assistant",
                        "content": content,
                        "requires_approval": True,
                        "approval": pending_approval.to_dict(),
                        "iterations": iteration + 1,
                        "division": division_id,
                    }
                
                # === OBSERVABILITY: tool (execute_tool) span ===
                tool_span = collector.start_span(trace_id, agent_span.id, "execute_tool", {
                    ATTR_TOOL_NAME: tool_name,
                })
                t_tool_start = time.time()
                
                result = await self.tools.call(tool_name, tool_args)
                
                tool_status = "error" if result.get("status") == "error" else "ok"
                collector.end_span(tool_span, status=tool_status, attributes={
                    ATTR_TOOL_NAME: tool_name,
                    "gen_ai.latency_ms": round((time.time() - t_tool_start) * 1000, 2),
                })
                
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
    
    def _precheck_approval(self, tool_name: str, tool_args: Dict[str, Any]):
        """Check if a tool action requires approval BEFORE execution.
        Returns ApprovalRequest if approval needed, else None."""
        from aeryn_core.safety.guardrail_engine import (
            get_guardrail_engine, GuardrailViolation, ApprovalRequired
        )
        engine = get_guardrail_engine()
        try:
            engine.check_tool(tool_name, tool_args)
            return None  # No approval needed
        except ApprovalRequired as e:
            return e.approval_request
        except GuardrailViolation:
            return None  # Will be caught as error in tool call

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
    
    async def run_stream(self, session_id: str, user_message: str, user_id: str = "default") -> AsyncGenerator[str, None]:
        """Run agent loop with TRUE token-by-token streaming."""
        from aeryn_core.utils.llm_client import get_mode_router
        from aeryn_core.runtime.error_recovery import get_error_recovery
        router = get_mode_router()
        session = router.get_or_create_session(session_id)
        recovery = get_error_recovery()
        
        # === DIVISION ROUTING ===
        division_id = self.divisions.classify(user_message)
        division_prompt = self.divisions.get_system_prompt(division_id)
        
        # === MEMORY RECALL ===
        relevant_memories = self.recall.recall(user_message, limit=3)
        memory_context = self.recall.format_for_prompt(relevant_memories)
        
        system_content = division_prompt
        if memory_context:
            system_content += "\n\n" + memory_context
        
        messages = [{"role": "system", "content": system_content}]
        messages.extend(session.messages)
        messages.append({"role": "user", "content": user_message})
        
        messages = self._trim_context(messages)
        
        tools_schema = self.tools.get_schemas()
        
        for iteration in range(self.max_iterations):
            # === TRUE STREAMING: token-by-token from LLM ===
            content = ""
            tool_calls = []
            stream_started = False
            
            async for piece in self.llm.chat_stream(
                messages=messages,
                session_id=session_id,
                tools=tools_schema
            ):
                chunk = json.loads(piece)
                if "content" in chunk:
                    token = chunk["content"]
                    content += token
                    # Stream each token to the frontend
                    yield json.dumps({"type": "token", "content": token})
                    stream_started = True
                elif "error" in chunk:
                    yield json.dumps({"type": "error", "error": chunk["error"]})
                    return
            
            if not content and not tool_calls:
                # No content and no tools — nothing to say
                yield json.dumps({"type": "done", "reason": "empty_response"})
                return
            
            # Emit the complete message marker
            yield json.dumps({"type": "message_complete", "content": content, "division": division_id})
            
            if not tool_calls:
                session.add_message("user", user_message)
                session.add_message("assistant", content)
                self._save_facts(session_id, user_message, content, messages)
                yield json.dumps({"type": "done", "reason": "complete"})
                return
            
            # Tool calls (no streaming for these — execute after)
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
                
                # === ERROR RECOVERY: retry tool call ===
                retry_result = await recovery.with_retry(
                    self.tools.call, tool_name, tool_args
                )
                if retry_result.success:
                    result = retry_result.result
                    if retry_result.attempts > 1:
                        yield json.dumps({"type": "tool_retry", "tool": tool_name, "attempts": retry_result.attempts})
                else:
                    result = {"error": f"tool '{tool_name}' failed after {retry_result.attempts} attempts: {retry_result.error}", "status": "error"}
                
                yield json.dumps({"type": "tool_result", "tool": tool_name, "result": result})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps(result),
                })
        
        yield json.dumps({"type": "done", "reason": "max_iterations"})
