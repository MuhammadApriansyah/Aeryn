import math
from typing import List, Dict

class AgnosticSemanticFeatureExtractor:
    def __init__(self):
        self.stop_words = {"the", "is", "at", "which", "on", "and", "a", "an", "to", "in", "of", "for", "with", "by", "as"}

    def tokenize_and_clean(self, text: str) -> List[str]:
        if not text:
            return []
        clean_text = "".join([c.lower() if c.isalnum() or c.isspace() else f" {c.lower()} " for c in text])
        return [word for word in clean_text.split() if word not in self.stop_words]

    def compute_local_entropy(self, tokens: List[str]) -> float:
        if not tokens:
            return 0.0
        frequency_map = {}
        for token in tokens:
            frequency_map[token] = frequency_map.get(token, 0) + 1
            
        total_tokens = len(tokens)
        entropy = 0.0
        for count in frequency_map.values():
            probability = count / total_tokens
            entropy -= probability * math.log2(probability)
        return round(entropy, 4)

    def extract_salient_entities(self, text: str, threshold_weight: float = 1.5) -> List[Dict]:
        tokens = self.tokenize_and_clean(text)
        if not tokens:
            return []
            
        frequency_map = {}
        for token in tokens:
            frequency_map[token] = frequency_map.get(token, 0) + 1
            
        entities = []
        for word, count in frequency_map.items():
            # Aturan Kaku: Menghitung bobot kepentingan berdasarkan panjang kata dan frekuensi kemunculan
            calculated_weight = count * (1.0 + (len(word) * 0.1))
            if calculated_weight >= threshold_weight:
                entities.append({
                    "entity_key": word,
                    "occurrence_count": count,
                    "saliency_weight": round(calculated_weight, 4)
                })
        return sorted(entities, key=lambda x: x["saliency_weight"], reverse=True)
