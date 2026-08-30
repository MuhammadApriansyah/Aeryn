#!/usr/bin/env python3
"""Rate Limiting — Built-in API rate limiter."""
import time
from typing import Dict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - 60
        
        if client_id not in self._requests:
            self._requests[client_id] = []
        
        self._requests[client_id] = [t for t in self._requests[client_id] if t > window_start]
        
        if len(self._requests[client_id]) >= self.rpm:
            return False
        
        self._requests[client_id].append(now)
        return True
    
    def get_middleware_code(self, framework: str = "fastify") -> str:
        if framework == "fastify":
            return """import rateLimit from '@fastify/rate-limit';
app.register(rateLimit, { max: 60, timeWindow: '1 minute' });
"""
        return ""

rate_limiter = RateLimiter()
