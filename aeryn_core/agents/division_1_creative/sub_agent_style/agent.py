class SubAgentLexicalStyleSwitcher:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, raw_llm_text: str, gate_mode: int) -> dict:
        if not raw_llm_text:
            return {"processed_text": "", "style_metrics": {"status": "EMPTY"}}
        styled_text = raw_llm_text
        if gate_mode == 0:
            styled_text = f"[TACTICAL ALERT] {raw_llm_text.upper()}"
        return {
            "processed_text": styled_text,
            "style_metrics": {"sub_agent_class": "STYLE_SWITCHER", "gate_applied": gate_mode}
        }
