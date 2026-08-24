import json


class PsychologicalAmigdalaOrchestrator:
    """Divisi psikologi — tensor emosi diturunkan dari teks percakapan nyata.

    V24 REAL-DATA: menggantikan mock_state hardcoded dengan analisis afektif
    leksikal + leaky integration temporal (state sesi sebelumnya memengaruhi
    state berikutnya).
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        from aeryn_core.agents.division_2_psych.sub_agents_real import (
            SubAgentLeakyIntegratorAccumulator,
            SubAgentMentalHealthCore,
            SubAgentPeaceKeeperEngine,
        )

        self.leaky_integrator = SubAgentLeakyIntegratorAccumulator(decay=0.7)
        self.mhc_core = SubAgentMentalHealthCore()
        self.peace_keeper = SubAgentPeaceKeeperEngine()

    def compile_psychological_vector_payload(self, user_id: str, logs: list, open_tasks: list,
                                             current_stimulus: str = "") -> dict:
        # Sumber analisis: stimulus aktif + jejak history terakhir
        texts = ([current_stimulus] if current_stimulus else []) + [str(l) for l in (logs or [])[-6:]]
        analyzed = self.leaky_integrator.analyze_text(texts)

        leaky_res = self.leaky_integrator.execute_sub_brain_reasoning(
            emotional_state_json=None, analyzed=analyzed, session_id=user_id
        )
        mhc_res = self.mhc_core.execute_sub_brain_reasoning(logs or [])
        peace_res = self.peace_keeper.execute_sub_brain_reasoning(open_tasks or [])

        stability = mhc_res["cognitive_stability"]
        stress = peace_res["internal_stress_index"]
        tensor = leaky_res["emotional_tensor"]

        recommended_gate = 3
        if stress > 0.5 or stability < 0.7:
            recommended_gate = 0          # DefensiveHostile → routing prioritas
        elif tensor["focus"] > 0.75 and tensor["pragmatism"] > 0.65:
            recommended_gate = 1          # HyperFocused

        payload = {
            "user_id": user_id,
            "recommended_gate": recommended_gate,
            "emotional_tensor_snapshot": {
                "pragmatism": tensor["pragmatism"],
                "hostility": round(max(tensor["hostility"], 0.9 if recommended_gate == 0 else 0.0), 4),
                "focus": tensor["focus"],
                "compassion": round(tensor["compassion"] * (1.0 - stress * 0.3), 4),
            },
            "affect_analysis": analyzed,
            "stress_index": stress,
            "stability": stability,
        }

        return {
            "recommended_gate": recommended_gate,
            "json_payload": json.dumps(payload, ensure_ascii=False),
        }
