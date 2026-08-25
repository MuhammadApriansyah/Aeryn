import hashlib

class SteganographicLogCipher:
    def __init__(self):
        self.registry = {}

    def embed_watermark_signal(self, payload_text: str, secret_key: str) -> str:
        if not payload_text or not secret_key:
            return payload_text
            
        hash_digest = hashlib.sha256(secret_key.encode('utf-8')).hexdigest()
        binary_signature = "".join(format(int(c, 16), '04b') for c in hash_digest[:8])
        
        words = payload_text.split(" ")
        watermarked_words = []
        
        for idx, word in enumerate(words):
            watermarked_words.append(word)
            if idx < len(binary_signature):
                bit = binary_signature[idx]
                if bit == "1":
                    watermarked_words.append("")
                    
        return " ".join(watermarked_words).strip()
