"""V39.60 — RateLimiter: extracted to separate module for reusability."""

import time
import threading
from collections import defaultdict, deque


class RateLimiter:
    """Token bucket rate limiter with per-key tracking."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()
    
    def allow(self, key: str) -> bool:
        """Check if request is allowed for key."""
        now = time.time()
        with self._lock:
            # Clean old entries
            while self._requests[key] and self._requests[key][0] < now - self.window:
                self._requests[key].popleft()
            if len(self._requests[key]) >= self.max_requests:
                return False
            self._requests[key].append(now)
            return True
    
    def reset(self, key: str = None):
        """Reset rate limiter for key or all."""
        with self._lock:
            if key:
                self._requests.pop(key, None)
            else:
                self._requests.clear()
    
    def get_stats(self, key: str) -> dict:
        """Get rate limiter stats for key."""
        now = time.time()
        with self._lock:
            # Clean old
            while self._requests[key] and self._requests[key][0] < now - self.window:
                self._requests[key].popleft()
            return {
                "key": key,
                "requests_in_window": len(self._requests[key]),
                "max_requests": self.max_requests,
                "window_seconds": self.window,
            }


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, max_failures: int = 3, base_wait: float = 1.0, max_wait: float = 60):
        self.max_failures = max_failures
        self.base_wait = base_wait
        self.max_wait = max_wait
        self._failures = 0
        self._last_failure = 0
        self._lock = threading.Lock()
    
    def record_failure(self):
        with self._lock:
            self._failures += 1
            self._last_failure = time.time()
    
    def record_success(self):
        with self._lock:
            self._failures = max(0, self._failures - 1)
    
    def is_opened(self) -> bool:
        return self._failures >= self.max_failures
    
    def should_skip(self) -> bool:
        if not self.is_opened():
            return False
        wait = min(self.base_wait * (2 ** (self._failures - self.max_failures)), self.max_wait)
        return time.time() - self._last_failure < wait
    
    def reset(self):
        with self._lock:
            self._failures = 0
            self._last_failure = 0


# Global registry for circuit breakers per provider
_cb_cache = {}
_cb_lock = threading.Lock()


def get_circuit_breaker(url: str, **kwargs) -> CircuitBreaker:
    """Get or create circuit breaker for URL."""
    with _cb_lock:
        if url not in _cb_cache:
            _cb_cache[url] = CircuitBreaker(**kwargs)
        return _cb_cache[url]


def get_rate_limiter(max_requests: int = 100, window_seconds: int = 60) -> RateLimiter:
    """Get a new rate limiter instance."""
    return RateLimiter(max_requests, window_seconds)
