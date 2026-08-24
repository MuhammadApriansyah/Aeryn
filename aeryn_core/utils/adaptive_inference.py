class AdaptiveInferenceBudgetController:
    def __init__(self, high_effort_threshold: float = 0.70):
        self.high_effort_threshold = high_effort_threshold
        self.session_budgets = {}

    def regulate_inference_regime(self, session_id: str, prompt_complexity: float, security_risk: float) -> dict:
        if session_id not in self.session_budgets:
            self.session_budgets[session_id] = {"total_tokens_consumed": 0, "high_effort_hits": 0}
            
        budget = self.session_budgets[session_id]
        combined_priority = (prompt_complexity * 0.4) + (security_risk * 0.6)
        
        is_high_effort = combined_priority >= self.high_effort_threshold
        allocated_max_predict = 1024 if is_high_effort else 512
        
        if is_high_effort:
            budget["high_effort_hits"] += 1
            
        return {
            "selected_compute_regime": "HIGH_EFFORT_SEARCH" if is_high_effort else "LOW_EFFORT_AUTOREGRESSIVE",
            "allocated_num_predict": allocated_max_predict,
            "priority_score": round(combined_priority, 4),
            "telemetry": {
                "high_effort_sequences_count": budget["high_effort_hits"]
            }
        }
