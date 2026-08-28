#!/usr/bin/env python3
"""V41.0 — Phase 1: Error Recovery System.

Features:
- Graceful degradation
- Auto-retry with exponential backoff
- Circuit breaker pattern
- Fallback mechanisms
- Error logging and alerting
"""

import os, json, time, asyncio, traceback
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"  # closed, open, half-open
    
    @property
    def is_open(self) -> bool:
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed > self.recovery_timeout:
                    self._state = "half-open"
                    return False
            return True
        return False
    
    def record_success(self):
        self._failure_count = 0
        self._state = "closed"
    
    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
    
    def get_state(self) -> Dict:
        return {
            "name": self.name,
            "state": self._state,
            "failure_count": self._failure_count,
            "is_open": self.is_open,
        }


class ErrorRecovery:
    """Central error recovery manager."""
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._error_log: list = []
        self._max_log_size = 1000
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name)
        return self._circuit_breakers[name]
    
    def log_error(self, error: Exception, context: str = "", severity: str = "error"):
        """Log error with context."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "severity": severity,
            "traceback": traceback.format_exc(),
        }
        self._error_log.append(entry)
        
        # Trim log if too large
        if len(self._error_log) > self._max_log_size:
            self._error_log = self._error_log[-self._max_log_size:]
    
    def get_error_log(self, limit: int = 50) -> list:
        return self._error_log[-limit:]
    
    def get_circuit_breaker_states(self) -> list:
        return [cb.get_state() for cb in self._circuit_breakers.values()]
    
    def get_stats(self) -> Dict:
        return {
            "total_errors": len(self._error_log),
            "circuit_breakers": len(self._circuit_breakers),
            "open_breakers": sum(1 for cb in self._circuit_breakers.values() if cb.is_open),
        }


def with_retry(max_retries: int = 3, base_delay: float = 1.0, exponential: bool = True):
    """Decorator for auto-retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt if exponential else 1)
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def with_fallback(fallback_value: Any = None):
    """Decorator for graceful fallback."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                return fallback_value
        return wrapper
    return decorator


def with_circuit_breaker(breaker_name: str):
    """Decorator for circuit breaker pattern."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            recovery = get_error_recovery()
            breaker = recovery.get_circuit_breaker(breaker_name)
            
            if breaker.is_open:
                raise Exception(f"Circuit breaker '{breaker_name}' is open")
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                recovery.log_error(e, context=breaker_name)
                raise
        return wrapper
    return decorator


# ── Singleton ─────────────────────────────────

_recovery: Optional[ErrorRecovery] = None

def get_error_recovery() -> ErrorRecovery:
    global _recovery
    if _recovery is None:
        _recovery = ErrorRecovery()
    return _recovery
