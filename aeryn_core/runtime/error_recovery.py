"""Error Recovery — auto-retry + fallback for tool/LLM failures.

Berdasarkan riset (Zylos Research): agent failure modes = "stuck tool loops,
runaway token costs, context propagation failures." Butuh auto-retry/fallback,
bukan cuma "max iterations reached".

Design:
- with_retry: exponential backoff retry untuk transient failure
- ToolFallback: kalau tool crash, coba tool alternatif
- GracefulDegradation: kalau gagal total, kembalikan partial result, bukan error polos
"""

import asyncio
import time
import inspect
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool
    result: Any = None
    attempts: int = 0
    error: str = ""
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "attempts": self.attempts,
            "error": self.error,
            "fallback_used": self.fallback_used,
        }


class ErrorRecovery:
    """Auto-retry with exponential backoff + fallback."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 8.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def with_retry(self, fn: Callable, *args, **kwargs) -> RetryResult:
        """Retry a function with exponential backoff."""
        last_error = ""

        for attempt in range(self.max_retries + 1):  # 1 initial + N retries
            try:
                if inspect.iscoroutinefunction(fn):
                    result = await fn(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(None, lambda: fn(*args, **kwargs))

                return RetryResult(success=True, result=result, attempts=attempt + 1)

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay)
                continue

        return RetryResult(success=False, attempts=self.max_retries + 1, error=last_error)

    async def with_fallback(self, primary: Callable, fallback: Callable, *args, **kwargs) -> RetryResult:
        """Try primary, fall back to alternative on failure."""
        result = await self.with_retry(primary, *args, **kwargs)
        if result.success:
            return result

        # Try fallback
        try:
            if inspect.iscoroutinefunction(fallback):
                fb_result = await fallback(*args, **kwargs)
            else:
                fb_result = await asyncio.get_event_loop().run_in_executor(None, lambda: fallback(*args, **kwargs))

            return RetryResult(success=True, result=fb_result, attempts=result.attempts, fallback_used=True)
        except Exception as e:
            return RetryResult(
                success=False,
                attempts=result.attempts,
                error=f"primary: {result.error}; fallback: {str(e)}",
                fallback_used=True,
            )


# Tool fallback mapping (primary -> alternatives)
TOOL_FALLBACKS: Dict[str, List[str]] = {
    "web_search": ["file_search"],  # if web fails, search local
    "bash": [],  # no safe fallback for bash
    "file_read": [],  # no fallback
}

# Global instance
_recovery = None

def get_error_recovery() -> ErrorRecovery:
    global _recovery
    if _recovery is None:
        _recovery = ErrorRecovery()
    return _recovery