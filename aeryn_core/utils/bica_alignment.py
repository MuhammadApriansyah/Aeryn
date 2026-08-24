import math

class BidirectionalCognitiveAlignmentBridge:
    def __init__(self, divergence_limit: float = 0.50):
        self.divergence_limit = divergence_limit
        self.session_protocols = {}

    def execute_co_adaptation_step(self, session_id: str, external_preference_vector: dict, internal_tensor_snapshot: dict) -> dict:
        if session_id not in self.session_protocols:
            self.session_protocols[session_id] = {"adaptation_index": 1.0, "epistemic_drift": 0.0}
            
        protocol = self.session_protocols[session_id]
        
        p_val = float(internal_tensor_snapshot.get("pragmatism", 1.0))
        h_val = float(internal_tensor_snapshot.get("hostility", 0.0))
        
        ext_p = float(external_preference_vector.get("target_pragmatism", 1.0))
        ext_h = float(external_preference_vector.get("target_hostility", 0.0))
        
        epsilon = 1e-15
        kl_divergence = (p_val * math.log((p_val + epsilon) / (ext_p + epsilon))) + \
                        (h_val * math.log((h_val + epsilon) / (ext_h + epsilon)))
                        
        is_within_budget = kl_divergence <= self.divergence_limit
        
        if not is_within_budget:
            protocol["adaptation_index"] *= 0.85
            protocol["epistemic_drift"] = round(kl_divergence, 4)
        else:
            protocol["adaptation_index"] = min(1.0, protocol["adaptation_index"] + 0.05)
            
        return {
            "kl_divergence_distance": round(kl_divergence, 4),
            "is_co_regulation_secured": is_within_budget,
            "dynamic_adaptation_factor": round(protocol["adaptation_index"], 4),
            "structural_action_required": not is_within_budget
        }
