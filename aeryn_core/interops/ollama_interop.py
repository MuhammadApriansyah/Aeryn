import json

class OfflineOllamaCognitiveBridge:
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance

    def execute_sovereign_local_chat(self, session_id: str, local_ollama_client, model_name: str, user_prompt: str, base_character_prompt: str = "System core authorized.") -> dict:
        mock_history = [{"text": "Local standalone turn active."}]
        mock_tasks = ["offline_environment_sync"]
        
        compiled_system_prompt = self.orchestrator.compile_stateful_system_prompt(
            session_id=session_id,
            base_character_prompt=base_character_prompt,
            user_prompt=user_prompt,
            mock_history_logs=mock_history,
            open_tasks=mock_tasks
        )
        
        messages_payload = [
            {"role": "system", "content": compiled_system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Eksekusi langsung ke library Ollama lokal yang tertanam di Termux tanpa rest-api eksternal
        raw_response = local_ollama_client.chat(model=model_name, messages=messages_payload)
        raw_text_output = raw_response.get("message", {}).get("content", "")
        
        digested_payload = self.orchestrator.digest_external_llm_response(
            session_id=session_id,
            user_prompt=user_prompt,
            raw_llm_output_text=raw_text_output
        )
        
        return {
            "user_visible_text": digested_payload["cleaned_response_text"],
            "cognitive_audit_trail": digested_payload["accounting_ledger_audit"]
        }
