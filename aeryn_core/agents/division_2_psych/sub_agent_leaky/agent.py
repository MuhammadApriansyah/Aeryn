import json

class SubAgentLeakyIntegratorAccumulator:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, emotional_state_json: str) -> dict:
        try:
            state = json.loads(emotional_state_json) if emotional_state_json else {}
        except Exception:
            state = {}
        pragmatism = float(state.get("pragmatism", 1.0)) * 0.9
        return {
            "decayed_pragmatism": round(pragmatism, 4),
            "integrator_metrics": {"sub_agent_class": "LEAKY_INTEGRATOR"}
        }
