import re

class VerifiableContextCompactor:
    def __init__(self, retention_limit: int = 4096):
        self.retention_limit = retention_limit

    def compact_reasoning_context(self, active_session_context: str, salient_entities_keys: list) -> dict:
        if not active_session_context:
            return {"compacted_context": "", "pruning_ratio": 0.0}
            
        sentences = re.split(r'(?<=[.!?])\s+', active_session_context)
        retained_sentences = []
        
        for sentence in sentences:
            lower_sentence = sentence.lower()
            is_anchor = any(str(key).lower() in lower_sentence for key in salient_entities_keys)
            
            is_proof_chain = any(kw in lower_sentence for kw in ["<think>", "</think>", "step", "verify", "assert"])
            
            if is_anchor or is_proof_chain:
                retained_sentences.append(sentence)
                
        compacted_text = " ".join(retained_sentences)
        
        orig_len = len(active_session_context)
        comp_len = len(compacted_text)
        pruning_ratio = 1.0 - (comp_len / max(1, orig_len))
        
        return {
            "compacted_context": compacted_text,
            "pruning_ratio": round(pruning_ratio, 4),
            "efficiency_metrics": {
                "original_char_length": orig_len,
                "compacted_char_length": comp_len
            }
        }
