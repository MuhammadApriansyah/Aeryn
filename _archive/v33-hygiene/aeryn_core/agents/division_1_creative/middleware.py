import json

class CreativeDivisionMiddleware:
    def __init__(self):
        self.middleware_brain_mode = "EVENT_DRIVEN_BLACKBOARD_OBSERVER"

    def process_blackboard_inbound_manifest(self, shared_blackboard_json: str) -> dict:
        """Otak Middleware: Menerima status telemetri, jika terdeteksi stresor kognitif, paksa pemotongan verbose."""
        try:
            blackboard_manifest = json.loads(shared_blackboard_json)
            extracted_gate_mode = blackboard_manifest.get("selected_gate_mode", 3)
            user_id = blackboard_manifest.get("user_id", "ANONYMOUS_USER")
            snapshot = blackboard_manifest.get("emotional_tensor_snapshot", {})
            
            # Reaktif: Jika hostility melonjak di atas 0.5, paksa pembatasan teks kaku
            pacing_modifier = 0.8 if snapshot.get("hostility", 0.0) > 0.5 else 1.0
        except Exception:
            extracted_gate_mode = 3
            user_id = "FALLBACK_USER"
            pacing_modifier = 1.0

        return {
            "selected_gate_mode": extracted_gate_mode,
            "target_user_id": user_id,
            "pacing_modifier": pacing_modifier,
            "middleware_clearance": True
        }

