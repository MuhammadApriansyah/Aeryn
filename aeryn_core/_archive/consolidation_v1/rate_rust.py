#!/usr/bin/env python3
"""
V41.0 — Rust RateLimiter wrapper.
Drop-in replacement untuk rate_limiter.py dengan performa Rust.
"""

from typing import Dict, Optional, Tuple
from aeryn_engine import RateLimiter as RustRateLimiter

class RateLimiter:
    """Wrapper Python untuk Rust RateLimiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._limiter = RustRateLimiter(max_requests, window_seconds)
        self._max_requests = max_requests
        self._window_seconds = window_seconds
    
    def check(self, key: str) -> Tuple[bool, int]:
        allowed, remaining = self._limiter.check(key)
        return allowed, int(remaining)
    
    def reset(self, key: str) -> None:
        self._limiter.reset(key)
    
    def stats(self) -> Dict:
        return self._limiter.stats()
    
    @property
    def max_requests(self) -> int:
        return self._max_requests
    
    @property
    def window_seconds(self) -> int:
        return self._window_seconds
