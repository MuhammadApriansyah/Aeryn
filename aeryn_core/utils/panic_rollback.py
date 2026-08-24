import time

class CognitivePanicRollbackController:
    def __init__(self, failure_threshold_consecutive: int = 3):
        self.max_failures = failure_threshold_consecutive
        self.session_fault_counters = {}
        self.stable_checkpoint_snapshots = {}

    def capture_stable_checkpoint(self, session_id: str, emotional_tensor: dict, structural_dag_state: dict) -> None:
        self.stable_checkpoint_snapshots[session_id] = {
            "emotional_tensor": emotional_tensor.copy(),
            "dag_state": structural_dag_state.copy(),
            "timestamp": int(time.time())
        }

    def increment_fault_and_evaluate_rollback(self, session_id: str) -> dict:
        if session_id not in self.session_fault_counters:
            self.session_fault_counters[session_id] = 0
            
        self.session_fault_counters[session_id] += 1
        trigger_rollback = self.session_fault_counters[session_id] >= self.max_failures
        
        restored_payload = {}
        if trigger_rollback and session_id in self.stable_checkpoint_snapshots:
            restored_payload = self.stable_checkpoint_snapshots[session_id]
            self.session_fault_counters[session_id] = 0
            
        return {
            "consecutive_fault_count": self.session_fault_counters[session_id],
            "panic_rollback_triggered": trigger_rollback,
            "restored_checkpoint_payload": restored_payload
        }

    def clear_fault_counter(self, session_id: str) -> None:
        self.session_fault_counters[session_id] = 0
