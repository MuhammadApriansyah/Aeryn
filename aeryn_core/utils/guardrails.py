import numpy as np

class CognitiveGuardrailEngine:
    def __init__(self, variance_threshold: float = -1.0):
        self.variance_threshold = variance_threshold

    def execute_semantic_outlier_detection(self, embedding_vector: list) -> bool:
        """Detect semantic outlier berdasarkan varians embedding.
        
        Returns True jika embedding dianggap outlier (varians sangat rendah
        = embedding mock/placeholder), False jika embedding valid.
        """
        if not embedding_vector or len(embedding_vector) == 0:
            return True
        
        vector_array = np.array(embedding_vector, dtype=np.float32)
        
        # Hitung varians — embedding valid punya varians signifikan
        vector_variance = float(np.var(vector_array) * 100.0)
        
        # Jika variance_threshold negatif (default), gunakan threshold adaptif
        threshold = self.variance_threshold if self.variance_threshold >= 0 else 0.01
        
        # Varians sangat rendah = embedding seragam = mock/placeholder
        if vector_variance < threshold:
            print(f"[GUARDRAIL_ALERT] Semantic variance anomaly: {vector_variance:.4f} < {threshold}")
            return True
        
        return False

