class AgenticReconsiderationGuard:
    def __init__(self, inertia_floor: float = 0.35):
        self.inertia_floor = inertia_floor
        self.active_commitments = {}

    def evaluate_commitment_trajectory(self, session_id: str, new_user_stimulus: str, emotional_stress_index: float) -> dict:
        if session_id not in self.active_commitments:
            self.active_commitments[session_id] = {"current_trajectory": "DEFAULT_STABLE_TRACK", "friction_load": 0.0}
            
        commitment = self.active_commitments[session_id]
        
        lower_stimulus = new_user_stimulus.lower() if new_user_stimulus else ""
        has_abort_signal = any(kw in lower_stimulus for kw in ["abort", "cancel", "stop", "change direction", "wait"])
        
        calculated_friction = (emotional_stress_index * 0.7) + (0.3 if has_abort_signal else 0.0)
        should_reconsider = calculated_friction > self.inertia_floor
        
        if should_reconsider:
            commitment["current_trajectory"] = "REDIRECTED_TACTICAL_TRACK"
            commitment["friction_load"] = calculated_friction
            
        return {
            "should_trigger_non_monotonic_step": should_reconsider,
            "reconsidered_trajectory_status": commitment["current_trajectory"],
            "calculated_computational_inertia": round(calculated_friction, 4)
        }
