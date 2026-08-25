import time

class InferenceTimeScalingBudget:
    def __init__(self, maximum_compute_budget: int = 10000):
        self.max_budget = maximum_compute_budget
        self.session_budgets = {}

    def allocate_dynamic_thinking_tokens(self, session_id: str, semantic_complexity_score: float) -> dict:
        if session_id not in self.session_budgets:
            self.session_budgets[session_id] = {"allocated_tokens": 0, "burst_count": 0}
            
        budget = self.session_budgets[session_id]
        
        base_tokens = 128
        scaled_tokens = min(2048, int(base_tokens * (1.0 + (semantic_complexity_score * 3.0))))
        
        budget["allocated_tokens"] += scaled_tokens
        budget["burst_count"] += 1
        
        return {
            "allocated_thinking_tokens": scaled_tokens,
            "is_within_safety_margin": budget["allocated_tokens"] <= self.max_budget,
            "telemetry": {
                "accumulated_session_cost": budget["allocated_tokens"],
                "total_burst_sequences": budget["burst_count"]
            }
        }
