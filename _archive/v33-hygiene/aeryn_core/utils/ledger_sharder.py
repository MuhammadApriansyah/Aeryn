import json
import time

class AgnosticLedgerShardManager:
    def __init__(self):
        self.isolated_shards = {}
        self.global_committed_ledger = []

    def commit_transaction_to_shard(self, session_id: str, source_division: int, allocation_delta: float) -> dict:
        if session_id not in self.isolated_shards:
            self.isolated_shards[session_id] = []
            
        shard = self.isolated_shards[session_id]
        tx_node = {
            "tx_id": f"TX_{session_id[:4].upper()}_{int(time.time()*1000)}",
            "division": source_division,
            "delta": allocation_delta,
            "timestamp": int(time.time())
        }
        shard.append(tx_node)
        return tx_node

    def merge_shard_to_global_ledger(self, session_id: str) -> dict:
        if session_id not in self.isolated_shards or not self.isolated_shards[session_id]:
            return {"merged_count": 0, "global_ledger_depth": len(self.global_committed_ledger)}
            
        shard_data = self.isolated_shards[session_id]
        merged_count = len(shard_data)
        
        self.global_committed_ledger.extend(shard_data)
        self.isolated_shards[session_id] = []
        
        return {
            "merged_count": merged_count,
            "global_ledger_depth": len(self.global_committed_ledger)
        }
