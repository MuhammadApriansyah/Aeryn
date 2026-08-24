import math

class LatentValueEvaluationNode:
    def __init__(self, baseline_threshold: float = 0.55):
        self.baseline_threshold = baseline_threshold
        self.trajectory_costs = {}

    def compute_monotone_fitness_score(self, session_id: str, raw_reasoning_fragment: str, total_tokens_spent: int) -> dict:
        if not raw_reasoning_fragment:
            return {"path_viable": False, "fitness_score": 0.0}
            
        if session_id not in self.trajectory_costs:
            self.trajectory_costs[session_id] = {"previous_fitness": 1.0, "cost_acc": 0}
            
        history = self.trajectory_costs[session_id]
        history["cost_acc"] += total_tokens_spent
        
        lower_frag = raw_reasoning_fragment.lower()
        logical_anchors = ["therefore", "because", "implies", "consistent", "conclude", "proof"]
        anchor_hits = sum(1 for anchor in logical_anchors if anchor in lower_frag)
        
        text_length = len(raw_reasoning_fragment)
        density_factor = float(anchor_hits * 100 / max(1, text_length))
        
        calculated_fitness = min(0.99, density_factor / (1.0 + math.log1p(history["cost_acc"] / 500.0)))
        
        is_viable = calculated_fitness >= self.baseline_threshold
        history["previous_fitness"] = calculated_fitness
        
        return {
            "path_viable": is_viable,
            "calculated_fitness_score": round(calculated_fitness, 4),
            "telemetry": {
                "accumulated_compute_cost": history["cost_acc"],
                "monotone_degradation_detected": calculated_fitness < history["previous_fitness"]
            }
        }
