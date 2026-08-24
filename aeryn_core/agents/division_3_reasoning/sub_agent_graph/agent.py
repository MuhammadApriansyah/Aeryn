
from typing import Any

class SubAgentEpistemicGraphTraverser:
    def __init__(self):
        self.internal_brain_mode = "EPISTEMIC_ADJACENCY_SCAN_ACTIVE"

    def execute_sub_brain_reasoning(self, rust_engine_instance: Any, text_prompt: str) -> dict:
        clean_prompt = text_prompt.lower()
        extracted_neighbors = []
        
        # Deteksi entitas aktif dari text kueri masuk untuk dijadikan titik start penjelajahan graf
        target_entity = None
        if "baseline" in clean_prompt or "tactical" in clean_prompt:
            target_entity = "tactical_baseline"
        elif "lockdown" in clean_prompt or "sector" in clean_prompt:
            target_entity = "sector_lockdown"
            
        if target_entity:
            extracted_neighbors = self.operational_skill.execute_bare_skill(rust_engine_instance, target_entity)
            
        return {
            "graph_search_hit": len(extracted_neighbors) > 0,
            "associated_concepts_retrieved": extracted_neighbors,
            "sub_agent_confidence": 0.98 if extracted_neighbors else 1.0
        }

