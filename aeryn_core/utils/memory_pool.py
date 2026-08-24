import time

class StatefulVolatileMemoryPool:
    def __init__(self, capacity_limit: int = 50):
        self.capacity_limit = capacity_limit
        self.shared_pool = {}

    def retain_volatile_state_segment(self, segment_key: str, data_payload: dict, ttl_seconds: int = 60) -> bool:
        if len(self.shared_pool) >= self.capacity_limit:
            oldest_key = min(self.shared_pool, key=lambda k: self.shared_pool[k]["expires_at"])
            del self.shared_pool[oldest_key]
            
        self.shared_pool[segment_key] = {
            "payload": data_payload,
            "expires_at": int(time.time()) + ttl_seconds
        }
        return True

    def fetch_active_state_segment(self, segment_key: str) -> dict:
        if segment_key not in self.shared_pool:
            return {}
            
        current_time = int(time.time())
        segment = self.shared_pool[segment_key]
        
        if current_time > segment["expires_at"]:
            del self.shared_pool[segment_key]
            return {}
            
        return segment["payload"]
