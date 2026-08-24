import re

class SubAgentNarrativeLedgerSynchronizer:
    def __init__(self):
        self.internal_brain_mode = "AGNOSTIC_COMPUTE_ACTIVE"

    def execute_sub_brain_reasoning(self, clean_narrative: str) -> dict:
        """
        Logika Murni Agnostik: Melakukan pemindaian teks cerita secara asinkron
        untuk mengekstrak entitas target transaksi keuangan secara mandiri.
        """
        if not clean_narrative:
            return {"sync_committed": False, "transactions_found": []}
            
        # Aturan Kaku: Deteksi pola angka kuantitas finansial di dalam narasi teks
        found_amounts = re.findall(r'\b\d+(?:\.\d+)?\b', clean_narrative)
        transactions = [{"amount": amt, "type": "AUTO_DETECTED"} for amt in found_amounts]
        
        return {
            "sync_committed": True,
            "transactions_found": transactions
        }
