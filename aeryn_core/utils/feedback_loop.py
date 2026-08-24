import json
import math

class CognitiveFeedbackLoopController:
    def __init__(self, target_entropy: float = 3.5):
        self.target_entropy = target_entropy
        self.error_history = {}

    def compute_proportional_derivative_correction(self, session_id: str, current_entropy: float) -> dict:
        if session_id not in self.error_history:
            self.error_history[session_id] = {"previous_error": 0.0, "integral_accumulation": 0.0}
            
        history = self.error_history[session_id]
        
        current_error = self.target_entropy - current_entropy
        derivative = current_error - history["previous_error"]
        history["integral_accumulation"] += current_error
        
        # Kalkulasi koreksi berbasis hukum kendali PID (Proportional-Integral-Derivative)
        bias_adjustment = (current_error * 0.5) + (derivative * 0.2) + (history["integral_accumulation"] * 0.05)
        history["previous_error"] = current_error
        
        return {
            "current_error_delta": round(current_error, 4),
            "proportional_derivative_bias": round(bias_adjustment, 4),
            "system_state": "STABLE" if abs(current_error) < 0.5 else "RE_REGULATION_REQUIRED"
        }
