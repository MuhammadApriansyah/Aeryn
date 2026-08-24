import time

class UniversalAgnosticCognitiveBridge:
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance

    def execute_sovereign_inference(self, session_id: str, provider_callback, user_prompt: str, base_character_prompt: str = "System core authorized.") -> dict:
        mock_history = [{"text": "Universal standalone session turn active."}]
        mock_tasks = ["offline_environment_sync"]
        
        # 1. GERBANG 1: Mengambil konstruksi prompt kaku dari Otak Aeryn
        compiled_system_prompt = self.orchestrator.compile_stateful_system_prompt(
            session_id=session_id,
            base_character_prompt=base_character_prompt,
            user_prompt=user_prompt,
            mock_history_logs=mock_history,
            open_tasks=mock_tasks
        )
        
        # 2. EKSEKUSI PENYUNTIKAN: Memanggil callback provider eksternal apa pun milikmu
        raw_text_output = provider_callback(compiled_system_prompt, user_prompt)
        
        # 3. GERBANG 2: Audit kelulusan teks, ekstraksi kas, dan konsolidasi memori
        digested_payload = self.orchestrator.digest_external_llm_response(
            session_id=session_id,
            user_prompt=user_prompt,
            raw_llm_output_text=raw_text_output
        )
        
        return {
            "cleaned_text": digested_payload["cleaned_response_text"],
            "ledger_audit": digested_payload["accounting_ledger_audit"]
        }
