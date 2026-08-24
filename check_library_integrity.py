import asyncio
import json

class ScriptAutomationTest:
    def __init__(self):
        self.test_session_id = "AUTOMATION_TEST_SESSION"
        self.base_doctrine = "System directive initialization core. User must shall follow instructions."
        self.user_stimulus = "Status report verification."
        self.mock_logs = [{"text": "Initializing automated baseline compliance check."}]
        self.mock_tasks = ["verify_system_integrity"]

    async def run_complete_library_pipeline_check(self):
        from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator
        orchestrator = UnifiedCognitiveOrchestrator(dimension=384, absolute_threshold=0.70)
        
        anchor_success = await orchestrator.register_agent_workflow_anchor(
            event_type="INTEGRATION_TEST",
            semantic_description="Automated component validation loop.",
            payload_config={"status": "INIT"}
        )
        
        if not anchor_success:
            return {"status": "FAILED", "reason": "Workflow anchor registration failed."}

        compiled_prompt = orchestrator.compile_stateful_system_prompt(
            session_id=self.test_session_id,
            base_character_prompt=self.base_doctrine,
            user_prompt=self.user_stimulus,
            mock_history_logs=self.mock_logs,
            open_tasks=self.mock_tasks
        )

        if not compiled_prompt:
            return {"status": "FAILED", "reason": "System prompt hydration compiler failed."}

        mock_llm_output = "<think>Validating core state tokens.</think> Tactical verification successful 100."

        digested_registry = orchestrator.digest_external_llm_response(
            session_id=self.test_session_id,
            user_prompt=self.user_stimulus,
            raw_llm_output_text=mock_llm_output
        )

        if digested_registry.get("status") != "SUCCESS_COMMIT":
            return {"status": "FAILED", "reason": "External response structural digestion failed."}

        return {
            "status": "SUCCESS",
            "compiled_prompt_sample": compiled_prompt,
            "cleaned_text_sample": digested_registry.get("cleaned_response_text")
        }

if __name__ == "__main__":
    tester = ScriptAutomationTest()
    result = asyncio.run(tester.run_complete_library_pipeline_check())
    print(json.dumps(result, indent=2))
