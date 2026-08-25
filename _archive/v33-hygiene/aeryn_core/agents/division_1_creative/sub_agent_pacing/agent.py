import re
import json

class SubAgentShannonEntropyPacingGuard:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    async def execute_sub_brain_reasoning_async(self, raw_llm_text: str) -> dict:
        thinking_tokens = re.findall(r'<think>(.*?)</think>', raw_llm_text, re.DOTALL)
        clean_narrative = re.sub(r'<think>.*?</think>', '', raw_llm_text, flags=re.DOTALL).strip()
        
        if "</think>" in raw_llm_text:
            clean_narrative = raw_llm_text.split("</think>")[-1].strip()

        tool_call_match = re.search(r'\{\s*"tool_name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}', clean_narrative, re.DOTALL)
        
        requires_react_feedback = False
        extracted_tool_payload = {}

        if tool_call_match:
            requires_react_feedback = True
            extracted_tool_payload = {
                "tool_name": tool_call_match.group(1),
                "arguments_json_string": tool_call_match.group(2)
            }

        return {
            "processed_text": clean_narrative,
            "metrics": {
                "sub_agent_class": "PACING_GUARD",
                "extracted_thinking_blocks": thinking_tokens,
                "tool_interception_triggered": requires_react_feedback,
                "extracted_tool_payload": extracted_tool_payload
            }
        }

