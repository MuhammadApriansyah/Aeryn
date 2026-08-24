import json

class EpistemicContextRouter:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.routing_tables = {}

    def compute_dynamic_routing_weight(self, session_id: str, semantic_complexity: float, emotional_intensity: float) -> dict:
        if session_id not in self.routing_tables:
            self.routing_tables[session_id] = {"pass_count": 0, "accumulated_load": 0.0}
            
        table = self.routing_tables[session_id]
        table["pass_count"] += 1
        
        calculated_priority = (semantic_complexity * 0.6) + (emotional_intensity * 0.4)
        target_allocation = "HIGH_COMPUTE_NODE" if calculated_priority > 0.65 else "STANDARD_COMPUTE_NODE"
        
        table["accumulated_load"] += calculated_priority
        
        return {
            "session_id": session_id,
            "calculated_priority": round(calculated_priority, 4),
            "target_allocation_node": target_allocation,
            "metrics": {
                "total_routed_passes": table["pass_count"],
                "historical_load_factor": round(table["accumulated_load"], 4)
            }
        }
