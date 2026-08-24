import json

class TransactionConsensusDirector:
    def __init__(self):
        from aeryn_core.agents.division_5_infra.sub_agent_sync.agent import SubAgentNarrativeLedgerSynchronizer
        from aeryn_core.agents.division_5_infra.sub_agent_validator.agent import SubAgentSagasTransactionValidator
        
        self.ledger_sync = SubAgentNarrativeLedgerSynchronizer()
        self.sagas_validator = SubAgentSagasTransactionValidator()

    def execute_infrastructure_accounting_sync(self, clean_narrative: str) -> dict:
        sync_res = self.ledger_sync.execute_sub_brain_reasoning(clean_narrative)
        val_res = self.sagas_validator.execute_sub_brain_reasoning(clean_narrative)
        
        payload = {
            "sync_committed": sync_res["sync_committed"],
            "equilibrium_secured": val_res["equilibrium_secured"],
            "detected_transactions": sync_res["transactions_found"],
            "audit_payload": val_res["infra_json_payload"]
        }
        
        return {
            "infra_json_payload": json.dumps(payload)
        }
