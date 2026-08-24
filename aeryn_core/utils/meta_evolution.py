import json
import time

class MetaPromptEvolutionDirector:
    def __init__(self, friction_ceiling: float = 0.80):
        self.friction_ceiling = friction_ceiling
        self.global_insight_repository = {}

    def record_reasoning_anomaly(self, session_id: str, division_code: int, failure_reason: str, critical_score: float) -> dict:
        if session_id not in self.global_insight_repository:
            self.global_insight_repository[session_id] = {
                "accumulated_friction": 0.0,
                "anomalies_logged": [],
                "meta_adjustment_applied": False
            }
            
        repo = self.global_insight_repository[session_id]
        repo["accumulated_friction"] += critical_score
        
        repo["anomalies_logged"].append({
            "division": division_code,
            "reason": failure_reason,
            "timestamp": int(time.time())
        })
        
        should_evolve = repo["accumulated_friction"] >= self.friction_ceiling
        if should_evolve:
            repo["meta_adjustment_applied"] = True
            
        return {
            "accumulated_session_friction": round(repo["accumulated_friction"], 4),
            "meta_prompt_evolution_triggered": should_evolve,
            "historical_anomaly_count": len(repo["anomalies_logged"])
        }

    def inject_evolutionary_bias_string(self, session_id: str, current_prompt: str) -> str:
        if session_id not in self.global_insight_repository:
            return current_prompt
            
        repo = self.global_insight_repository[session_id]
        if repo["meta_adjustment_applied"]:
            return f"{current_prompt} [META_PROMPT_EVOLUTION: ENFORCE_MAXIMAL_COMPUTATIONAL_VIGILANCE_CRITICAL_ANOMALY_DETECTED]"
        return current_prompt
