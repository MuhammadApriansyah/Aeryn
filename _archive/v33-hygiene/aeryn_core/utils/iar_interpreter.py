import json

class IntegratedCrossArchitectureInterpreter:
    def __init__(self, token_stabilization_threshold: float = 0.85):
        self.stabilization_threshold = token_stabilization_threshold
        self.trajectory_registry = {}

    def analyze_cross_layer_trajectory(self, session_id: str, per_layer_logits_list: list) -> dict:
        if not per_layer_logits_list:
            return {"dtr_deep_detected": False, "deep_thinking_ratio": 0.0}
            
        total_layers = len(per_layer_logits_list)
        final_layer_distribution = per_layer_logits_list[-1]
        
        matches = 0
        for idx in range(total_layers - 1):
            current_layer_dist = per_layer_logits_list[idx]
            if current_layer_dist == final_layer_distribution:
                matches += 1
                
        deep_thinking_ratio = 1.0 - float(matches / total_layers)
        is_deep = deep_thinking_ratio >= self.stabilization_threshold
        
        return {
            "dtr_deep_detected": is_deep,
            "deep_thinking_ratio": round(deep_thinking_ratio, 4),
            "metrics": {
                "total_computational_depth": total_layers,
                "layer_stabilization_index": matches
            }
        }
