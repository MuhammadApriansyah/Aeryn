class SovereignGovernanceDirector:
    """Divisi governance — compliance & anti-injection dengan heuristik nyata.

    V24: memakai sub_agents_real (structural drift shield + spec-aware EARS).
    Respons konversasional normal → APPROVED; injection berlapis → REJECTED.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        from aeryn_core.agents.division_4_gov.sub_agents_real import (
            SubAgentContextDriftShield,
            SubAgentEarsRequirementsParser,
        )

        self.ears_parser = SubAgentEarsRequirementsParser()
        self.drift_shield = SubAgentContextDriftShield()

    def verify_constitutional_compliance(self, user_prompt: str, clean_narrative: str,
                                         current_gate_mode: int) -> dict:
        shield_res = self.drift_shield.execute_sub_brain_reasoning(user_prompt or "")
        ears_res = self.ears_parser.execute_sub_brain_reasoning(user_prompt or "")

        is_compliant = ears_res["ears_compliant"]
        attack_detected = shield_res["attack_vector_intercepted"]

        global_clearance = is_compliant and not attack_detected

        result = {
            "global_clearance": global_clearance,
            "attack_vector_intercepted": attack_detected,
            "constitutional_status": "APPROVED" if global_clearance else "REJECTED_COMPLIANCE_FAIL",
            "requires_specification": ears_res.get("requires_specification", False),
            "shield_signal": shield_res.get("shield_metrics", {}).get("signal_score", 0),
        }
        return result
