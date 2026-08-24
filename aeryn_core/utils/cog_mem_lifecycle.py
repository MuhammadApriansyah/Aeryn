import time
import re

class CognitiveSustainedMemoryLifecycle:
    def __init__(self, long_term_threshold: float = 0.75):
        self.focus_of_attention = {}
        self.direct_access_memory = {}
        self.long_term_consolidation = {}
        self.lt_threshold = long_term_threshold

    def ingest_working_tokens(self, session_id: str, turn_id: str, factual_content: str, emotional_weight: float) -> dict:
        self.focus_of_attention[session_id] = {
            "turn_id": turn_id,
            "content": factual_content,
            "weight": emotional_weight,
            "ingested_at": time.time()
        }
        
        if session_id not in self.direct_access_memory:
            self.direct_access_memory[session_id] = []
            
        self.direct_access_memory[session_id].append({
            "content": factual_content,
            "score": emotional_weight,
            "timestamp": int(time.time())
        })
        
        should_consolidate = emotional_weight >= self.lt_threshold
        if should_consolidate:
            entity_keys = re.findall(r'\b[A-Z][a-z0-9_]+\b', factual_content)
            for key in entity_keys:
                self.long_term_consolidation[f"{session_id}::{key}"] = {
                    "abstract_chunk": factual_content,
                    "compiled_at": int(time.time())
                }
                
        return {
            "focus_segment_retained": True,
            "compiled_chunks_count": len(self.long_term_consolidation),
            "delegation_required": should_consolidate
        }
