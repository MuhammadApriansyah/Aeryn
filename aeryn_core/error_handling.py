"""V39.60 — Standardized error handling and Result types."""

from typing import Any, Tuple


class Result:
    """Standardized result type for operations that can fail."""
    
    def __init__(self, is_ok: bool, value: Any = None, error: str = "", fallback: str = ""):
        self._is_ok = is_ok
        self.value = value
        self.error = error
        self.fallback = fallback
    
    @property
    def ok(self) -> bool:
        return self._is_ok
    
    @property
    def is_ok(self) -> bool:
        return self._is_ok
    
    @property
    def is_err(self) -> bool:
        return not self._is_ok
    
    @classmethod
    def success(cls, value: Any = None) -> "Result":
        return cls(is_ok=True, value=value)
    
    @classmethod
    def fail(cls, error: str, fallback: str = "") -> "Result":
        return cls(is_ok=False, error=error, fallback=fallback)
    
    def unwrap(self) -> Any:
        """Get value or raise exception."""
        if not self._is_ok:
            raise RuntimeError(f"Unwrap failed: {self.error}")
        return self.value
    
    def unwrap_or(self, default: Any) -> Any:
        """Get value or return default."""
        return self.value if self._is_ok else default


def safe_call(func, *args, fallback: str = "", **kwargs) -> Result:
    """Call a function safely, returning a Result."""
    try:
        result = func(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        return Result.fail(str(e), fallback)


def get_fallback_for_operation(operation: str, error: str) -> str:
    """Get human-readable fallback directive for an operation."""
    fallbacks = {
        "safety_check": {
            "timeout": "FALLBACK: Allow request but flag for review",
            "error": "FALLBACK: Log error and continue with restricted mode",
        },
        "search": {
            "no_results": "FALLBACK: Try broader query or check memory",
            "timeout": "FALLBACK: Return cached results if available",
            "error": "FALLBACK: Fall back to simple keyword match",
        },
        "adapter_selection": {
            "no_match": "FALLBACK: Use generic explain adapter",
            "error": "FALLBACK: Continue without adapter",
        },
        "memory_write": {
            "full": "FALLBACK: Clear old entries and retry",
            "error": "FALLBACK: Store in temporary memory",
        },
        "memory_read": {
            "not_found": "FALLBACK: Search related topics",
            "error": "FALLBACK: Return empty result gracefully",
        },
        "prompt_compile": {
            "error": "FALLBACK: Use minimal prompt template",
        },
        "output_validate": {
            "leak": "FALLBACK: Sanitize and retry",
            "error": "FALLBACK: Return safe error message",
        },
    }
    
    op_fallbacks = fallbacks.get(operation, {})
    for key, directive in op_fallbacks.items():
        if key in error.lower():
            return directive
    
    return f"FALLBACK: {operation} failed ({error}), try alternative approach"


class AerynError(Exception):
    """Base exception for Aeryn with fallback directive."""
    
    def __init__(self, message: str, fallback: str = ""):
        super().__init__(message)
        self.fallback = fallback
        self.message = message


class SafetyError(AerynError):
    """Safety violation."""
    pass


class SearchError(AerynError):
    """Search operation failed."""
    pass


class MemoryError(AerynError):
    """Memory operation failed."""
    pass


class AdapterError(AerynError):
    """Adapter operation failed."""
    pass
