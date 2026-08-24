class ReasoningDivisionMiddleware:
    def __init__(self):
        self.middleware_brain_mode = "DYNAMIC_COMPUTE_BUDGET_ADJUDICATOR"

    def enforce_temporal_compute_budget(self, exploration_depth: int, latency_spike_alert: bool) -> dict:
        """Otak Middleware: Jika Rust Core memancarkan sinyal telemetri spike, potong budget kedalaman pohon MCTS secara instan."""
        base_depth = min(max(exploration_depth, 1), 50)
        if latency_spike_alert:
            # Pangkas kedalaman eksplorasi 50% untuk menyelamatkan RAM hardware dari ancaman freeze
            base_depth = max(base_depth // 2, 2)
            print("[MIDDLEWARE_DIV_III] Cognitive saturation detected. Adaptive compute budget downscaled.")
            
        return {
            "sanitized_exploration_depth": base_depth,
            "middleware_clearance": True
        }

