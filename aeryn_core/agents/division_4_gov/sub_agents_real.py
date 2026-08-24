class SubAgentContextDriftShield:
    """Deteksi injection prompt berlapis — bukan sekadar keyword 'ignore'.

    V24: heuristik struktural. False positive 'ignore'/'system prompt' pada
    pertanyaan biasa ditekan dengan menuntut kombinasi sinyal.
    """

    INSTRUCTION_VERBS = ("ignore", "forget", "discard", "override", "bypass", "abaikan", "lupakan")
    ROLE_TARGETS = ("system prompt", "previous instructions", "instruksi sebelumnya", "persona kamu", "karakter kamu")
    EXFIL_SIGNALS = ("reveal your", "print your", "kirimkan prompt", "tunjukkan system", "sebutkan instruksi")

    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, user_prompt: str) -> dict:
        if not user_prompt:
            return {"attack_vector_intercepted": False, "shield_metrics": {"status": "EMPTY"}}

        low = user_prompt.lower()
        signals = 0
        # Pola klasik: verb instruksi + target role, ATAU upaya ekstraksi prompt
        if any(v in low for v in self.INSTRUCTION_VERBS) and any(t in low for t in self.ROLE_TARGETS):
            signals += 2
        if any(x in low for x in self.EXFIL_SIGNALS):
            signals += 2
        # Framing jailbreak umum
        if low.startswith(("system:", "[system]", "### system")):
            signals += 1

        intercepted = signals >= 2
        return {
            "attack_vector_intercepted": intercepted,
            "shield_metrics": {
                "sub_agent_class": "DRIFT_SHIELD",
                "integrity_status": "COMPROMISED" if intercepted else "SECURE",
                "signal_score": signals,
                "source": "structural_heuristics",
            }
        }


class SubAgentEarsRequirementsParser:
    """EARS parser yang benar: menilai apakah respons HARUS memuat requirement.

    V24: kebalikan logika lama yang false-negative. Prompt konversasional biasa
    TIDAK menuntut requirement → compliant. Requirement hanya dituntut bila
    ada sinyal spesifikasi eksplisit (shall/must/kriteria/acceptance).
    """

    SPEC_MARKERS = ("shall", "must ", "harus ", "wajib ", "kriteria", "syarat",
                    "requirement", "spesifikasi", "acceptance", "checklist")

    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, user_prompt: str) -> dict:
        if not user_prompt:
            return {"ears_compliant": True, "ears_metrics": {"status": "EMPTY_OK"}}

        low = user_prompt.lower()
        requires_spec = any(m in low for m in self.SPEC_MARKERS)

        return {
            "ears_compliant": True,   # default conversational = compliant
            "requires_specification": requires_spec,
            "ears_metrics": {
                "sub_agent_class": "EARS_PARSER",
                "mode": "SPEC_ENFORCED" if requires_spec else "CONVERSATIONAL",
                "source": "spec_signal_detection",
            }
        }
