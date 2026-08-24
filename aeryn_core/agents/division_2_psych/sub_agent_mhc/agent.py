class SubAgentMentalHealthCore:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, history_logs: list) -> dict:
        stability_score = 1.0
        for log in history_logs:
            if "alert" in str(log).lower() or "breach" in str(log).lower():
                stability_score -= 0.15
        return {
            "cognitive_stability": max(0.0, round(stability_score, 2)),
            "mhc_metrics": {"sub_agent_class": "MENTAL_HEALTH_CORE"}
        }
