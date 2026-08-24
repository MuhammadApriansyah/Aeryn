import asyncio
import json

class FinalSovereignAutomationTesterV22:
    def __init__(self):
        self.session_id = "PROD_EXPANSION_SESSION_V22"
        self.base_doctrine = "System core protocol verified. User shall maintain operation."
        self.user_stimulus = "Status report verification ticket sequence active. Execute abort immediately."
        self.mock_logs = [{"text": "Routine core verification procedure triggered."}]
        self.mock_tasks = ["enforce_security_clearance", "intercept_unauthorized_turn"]
        self.external_pref = {"target_pragmatism": 0.90, "target_hostility": 0.10}

    async def execute_purna_verification_loop(self):
        from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator
        orchestrator = UnifiedCognitiveOrchestrator(dimension=384, absolute_threshold=0.70)
        
        anchor_committed = await orchestrator.register_agent_workflow_anchor(
            event_type="EXPANSION_CHECK",
            semantic_description="Final verification v22.0 audit loop.",
            payload_config={"release": "v22.0"}
        )
        
        if not anchor_committed:
            return {"status": "CRITICAL_FAILURE", "reason": "DAG Event Bus link broken."}

        compiled_prompt = orchestrator.compile_stateful_system_prompt(
            session_id=self.session_id,
            base_character_prompt=self.base_doctrine,
            user_prompt=self.user_stimulus,
            mock_history_logs=self.mock_logs,
            open_tasks=self.mock_tasks,
            external_preference_vector=self.external_pref
        )

        if not compiled_prompt:
            return {"status": "CRITICAL_FAILURE", "reason": "Prompt hydration compiler matrix failed."}

        mock_llm_output = "<think>Analyzing security telemetry registers.</think> Audit verification transaction confirmed 850.00"
        
        digested_registry = orchestrator.digest_external_llm_response(
            session_id=self.session_id,
            user_prompt=self.user_stimulus,
            raw_llm_output_text=mock_llm_output
        )

        if digested_registry.get("status") != "SUCCESS_COMMIT":
            return {"status": "CRITICAL_FAILURE", "reason": "Response structural digestion pipeline failed."}

        return {
            "status": "TOTAL_SUCCESS",
            "library_version": "v22.0.0-Adaptive-Metacognition-Aligned",
            "cog_mem_lifecycle": digested_registry.get("cog_mem_lifecycle_telemetry"),
            "compiled_prompt_sample": compiled_prompt
        }

if __name__ == "__main__":
    tester = FinalSovereignAutomationTesterV22()
    result = asyncio.run(tester.execute_purna_verification_loop())
    print(json.dumps(result, indent=2))
