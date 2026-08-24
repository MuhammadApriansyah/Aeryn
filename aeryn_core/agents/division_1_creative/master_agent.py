from typing import List

class CreativeDivisionDirector:
    def __init__(self, dimension: int = 384, target_min: int = 19000, target_max: int = 36500):
        self.dimension = dimension
        self.target_min_chars = target_min
        self.target_max_chars = target_max
        from aeryn_core.agents.division_1_creative.sub_agent_pov.agent import SubAgentDeepPovEnforcer
        from aeryn_core.agents.division_1_creative.sub_agent_style.agent import SubAgentLexicalStyleSwitcher
        
        self.pov_enforcer = SubAgentDeepPovEnforcer()
        self.style_switcher = SubAgentLexicalStyleSwitcher()

    def compile_sovereign_system_prompt_node(self, base_character_prompt: str, shared_blackboard_json: str, associated_graph_memories: list, tools_manifest: str = "") -> str:
        import json
        try:
            parsed_blackboard = json.loads(shared_blackboard_json) if shared_blackboard_json else {}
        except Exception:
            parsed_blackboard = {}
            
        gate_mode = parsed_blackboard.get("recommended_gate", 3)
        
        system_prompt = base_character_prompt
        
        pov_res = self.pov_enforcer.execute_sub_brain_reasoning(system_prompt)
        system_prompt = pov_res["processed_text"]
        
        style_res = self.style_switcher.execute_sub_brain_reasoning(system_prompt, gate_mode)
        system_prompt = style_res["processed_text"]
        
        if associated_graph_memories:
            graph_string = " | ".join([f"Entity: {m}" for m in associated_graph_memories])
            system_prompt += f"\n[EPISTEMIC_KNOWLEDGE_GRAPH_RETRIEVED_MEMORIES: {graph_string}]"

        if tools_manifest:
            system_prompt += f"\n\n[ENVIRONMENT_AWARENESS_AVAILABLE_TOOLS_SCHEMA]\n{tools_manifest}"

        return system_prompt
