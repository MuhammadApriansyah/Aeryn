import time

class AttentionGuidedEvictionStore:
    def __init__(self, hot_capacity: int = 5, recency_alpha: float = 0.7):
        self.hot_capacity = hot_capacity
        self.recency_alpha = recency_alpha
        self.hot_buffer = {}
        self.cold_store = {}

    def touch_and_evict_stale_nodes(self, session_id: str, active_keys: list) -> dict:
        current_time = time.time()
        if session_id not in self.hot_buffer:
            self.hot_buffer[session_id] = {}
        if session_id not in self.cold_store:
            self.cold_store[session_id] = {}
            
        session_hot = self.hot_buffer[session_id]
        
        for key in active_keys:
            if key in self.cold_store[session_id]:
                session_hot[key] = self.cold_store[session_id].pop(key)
            if key not in session_hot:
                session_hot[key] = {"hits": 0, "score": 1.0, "last_used": current_time}
            
            node = session_hot[key]
            node["hits"] += 1
            node["score"] = (node["score"] * (1.0 - self.recency_alpha)) + (1.0 * self.recency_alpha)
            node["last_used"] = current_time

        for k, v in session_hot.items():
            if k not in active_keys:
                time_delta = current_time - v["last_used"]
                v["score"] *= max(0.1, 1.0 - (time_delta * 0.05))

        evicted = []
        if len(session_hot) > self.hot_capacity:
            sorted_keys = sorted(session_hot.keys(), key=lambda x: session_hot[x]["score"])
            while len(session_hot) > self.hot_capacity:
                evict_key = sorted_keys.pop(0)
                self.cold_store[session_id][evict_key] = session_hot.pop(evict_key)
                evicted.append(evict_key)

        return {
            "active_hot_count": len(session_hot),
            "evicted_to_cold_keys": evicted,
            "cold_store_depth": len(self.cold_store[session_id])
        }
