#!/usr/bin/env python3
"""V1.0 — APIGateway: unified routing, auth, rate limiting, and response caching.

Integrates with:
  - auth_manager.AuthManager   (RBAC, session tokens)
  - rate_limiter.RateLimiter   (token-bucket per-key)
  - rate_limiter.CircuitBreaker (fault isolation)
  - error_handling.Result      (structured error returns)
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from .auth_manager import get_auth
from .error_handling import Result, AerynError
from .rate_limiter import RateLimiter, CircuitBreaker, get_circuit_breaker
from .config import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW, CB_MAX_FAILURES, CB_BASE_WAIT, CB_MAX_WAIT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class Request:
    """Incoming request envelope."""
    method: HTTPMethod
    path: str                          # e.g. "/v1/tools/list"
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    remote_addr: str = "127.0.0.1"

    # Convenience -------------------------------------------------------
    @property
    def auth_token(self) -> Optional[str]:
        return self.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None

    @property
    def cache_key(self) -> str:
        """Deterministic key for identical requests (method + path + body)."""
        raw = f"{self.method.value}:{self.path}:{json.dumps(self.body, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class Response:
    """Outgoing response envelope."""
    status_code: int = 200
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    cached: bool = False

    def to_dict(self) -> dict:
        return {
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
            "cached": self.cached,
        }


# Type alias for handler functions
HandlerFn = Callable[[Request], Union[Response, Result]]


# ---------------------------------------------------------------------------
# LRU cache (thread-safe)
# ---------------------------------------------------------------------------

class _LRUCache:
    """Simple thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 256, default_ttl: float = 30.0):
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._store: OrderedDict[str, Tuple[float, Response]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    # -- public API -------------------------------------------------------

    def get(self, key: str) -> Optional[Response]:
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None
            expires_at, value = self._store[key]
            if time.time() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._store.move_to_end(key)
            self._hits += 1
            value.cached = True
            return value

    def put(self, key: str, value: Response, ttl: Optional[float] = None) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]
            elif len(self._store) >= self._max_size:
                self._store.popitem(last=False)
            self._store[key] = (time.time() + (ttl if ttl is not None else self._default_ttl), value)

    def invalidate(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys whose *request path* starts with *prefix*."""
        # We can't reverse the hash, so this is best-effort via a parallel index.
        # For simplicity we clear the entire cache when prefix-mutation happens.
        # A production version would maintain a path -> [keys] index.
        count = len(self._store)
        self._store.clear()
        return count

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / max(1, self._hits + self._misses),
            }


# ---------------------------------------------------------------------------
# Route registry
# ---------------------------------------------------------------------------

@dataclass
class _Route:
    method: HTTPMethod
    path: str                        # exact path or prefix
    handler: HandlerFn
    require_auth: bool = True
    required_permission: Optional[str] = None
    cache_ttl: Optional[float] = None  # None = no cache
    rate_limit_key: Optional[str] = None  # None = use remote_addr
    description: str = ""


# ---------------------------------------------------------------------------
# Middleware chain
# ---------------------------------------------------------------------------

MiddlewareFn = Callable[[Request, Callable[[], Response]], Response]


# ---------------------------------------------------------------------------
# APIGateway
# ---------------------------------------------------------------------------


class APIGateway:
    """Unified API gateway for Aeryn-Core.

    Usage::

        gw = APIGateway()
        gw.route("GET", "/v1/tools", list_tools_handler, cache_ttl=60)
        gw.route("POST", "/v1/tools/run", run_tool_handler, required_permission="write")
        response = gw.handle(request)
    """

    def __init__(
        self,
        auth_manager=None,
        rate_limiter: Optional[RateLimiter] = None,
        cache_max_size: int = 256,
        cache_ttl: float = 30.0,
        enable_circuit_breaker: bool = True,
    ):
        self.auth = auth_manager or get_auth()
        self.rate_limiter = rate_limiter or RateLimiter(RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
        self.cache = _LRUCache(max_size=cache_max_size, default_ttl=cache_ttl)
        self._enable_cb = enable_circuit_breaker
        self._routes: List[_Route] = []
        self._middleware: List[MiddlewareFn] = []
        self._lock = threading.Lock()

        # ---- logging middleware (always first) ----
        self._middleware.append(self._logging_middleware)

    # ===================================================================
    # Route registration
    # ===================================================================

    def route(
        self,
        method: str,
        path: str,
        handler: HandlerFn,
        *,
        require_auth: bool = True,
        required_permission: Optional[str] = None,
        cache_ttl: Optional[float] = None,
        rate_limit_key: Optional[str] = None,
        description: str = "",
    ) -> "APIGateway":
        """Register a handler for *method* + *path*.

        Returns *self* for chaining::

            gw.route("GET", "/a", h1).route("POST", "/b", h2)
        """
        rt = _Route(
            method=HTTPMethod(method.upper()),
            path=path,
            handler=handler,
            require_auth=require_auth,
            required_permission=required_permission,
            cache_ttl=cache_ttl,
            rate_limit_key=rate_limit_key,
            description=description,
        )
        with self._lock:
            self._routes.append(rt)
        logger.debug("route registered: %s %s -> %s", rt.method.value, path, description or handler.__name__)
        return self

    # Convenience decorators -------------------------------------------

    def get(self, path: str, **kwargs):
        """Decorator shortcut for ``route("GET", ...)``."""
        def deco(fn):
            self.route("GET", path, fn, **kwargs)
            return fn
        return deco

    def post(self, path: str, **kwargs):
        def deco(fn):
            self.route("POST", path, fn, **kwargs)
            return fn
        return deco

    # ===================================================================
    # Middleware
    # ===================================================================

    def add_middleware(self, mw: MiddlewareFn) -> "APIGateway":
        """Insert a custom middleware.  Inserted *after* the logger."""
        self._middleware.insert(1 if self._middleware else 0, mw)
        return self

    # ===================================================================
    # Core dispatch
    # ===================================================================

    def handle(self, request: Request) -> Response:
        """Process *request* through the full pipeline and return a Response."""

        # ---- resolve route ----
        matched = self._find_route(request.method, request.path)
        if matched is None:
            return Response(status_code=404, body={"error": "not_found", "path": request.path})

        route = matched

        # ---- rate limiting ----
        rl_key = route.rate_limit_key or request.remote_addr
        if not self.rate_limiter.allow(rl_key):
            stats = self.rate_limiter.get_stats(rl_key)
            return Response(
                status_code=429,
                body={
                    "error": "rate_limit_exceeded",
                    "retry_after": RATE_LIMIT_WINDOW,
                    "stats": stats,
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )

        # ---- authentication ----
        if route.require_auth:
            token = request.auth_token
            if not token:
                return Response(status_code=401, body={"error": "unauthorized", "detail": "missing Bearer token"})
            if not self._verify_token(token):
                return Response(status_code=401, body={"error": "unauthorized", "detail": "invalid or expired token"})

        # ---- authorization ----
        if route.required_permission:
            token = request.auth_token
            if not self.auth.check_permission(token, route.required_permission):
                return Response(
                    status_code=403,
                    body={"error": "forbidden", "permission": route.required_permission},
                )

        # ---- cache lookup (GET only, only if configured) ----
        if route.cache_ttl is not None and request.method == HTTPMethod.GET:
            cached = self.cache.get(request.cache_key)
            if cached is not None:
                cached.headers["X-Cache"] = "HIT"
                return cached

        # ---- circuit breaker (if enabled and route has one) ----
        if self._enable_cb:
            cb = get_circuit_breaker(
                f"{route.method.value}:{route.path}",
                max_failures=CB_MAX_FAILURES,
                base_wait=CB_BASE_WAIT,
                max_wait=CB_MAX_WAIT,
            )
            if cb.should_skip():
                return Response(
                    status_code=503,
                    body={"error": "service_unavailable", "detail": "circuit breaker open"},
                )

        # ---- execute via middleware chain ----
        def _invoke() -> Response:
            try:
                raw = route.handler(request)
                if isinstance(raw, Result):
                    if raw.is_ok:
                        resp = Response(status_code=200, body=raw.value)
                    else:
                        resp = Response(status_code=400, body={"error": raw.error, "fallback": raw.fallback})
                elif isinstance(raw, Response):
                    resp = raw
                else:
                    resp = Response(status_code=200, body=raw)
            except AerynError as e:
                if self._enable_cb:
                    cb.record_failure()
                resp = Response(status_code=500, body={"error": e.message, "fallback": e.fallback})
            except Exception as e:
                if self._enable_cb:
                    cb.record_failure()
                logger.exception("unhandled exception in handler for %s %s", route.method.value, route.path)
                resp = Response(status_code=500, body={"error": "internal_error", "detail": str(e)})
            else:
                if self._enable_cb:
                    cb.record_success()
            return resp

        # Build chain properly (avoid late-binding trap)
        chain: Callable[[], Response] = _invoke
        for mw in reversed(self._middleware):
            chain = self._wrap(mw, chain, request)

        response = chain()

        # ---- cache store ----
        if route.cache_ttl is not None and request.method == HTTPMethod.GET and response.status_code < 400:
            self.cache.put(request.cache_key, response, ttl=route.cache_ttl)
            response.headers["X-Cache"] = "MISS"

        return response

    # ===================================================================
    # Auth helpers (thin wrappers for clarity)
    # ===================================================================

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return a session token."""
        return self.auth.authenticate(username, password)

    def check_permission(self, token: str, permission: str) -> bool:
        """Check whether *token* carries *permission*."""
        return self.auth.check_permission(token, permission)

    def rate_limit(self, key: str) -> bool:
        """Check if a request from *key* is within rate limits."""
        return self.rate_limiter.allow(key)

    # ===================================================================
    # Cache management
    # ===================================================================

    def cache_response(self, key: str, response: Response, ttl: Optional[float] = None) -> None:
        """Manually cache a response under *key*."""
        self.cache.put(key, response, ttl=ttl)

    def cache_invalidate(self, key: str) -> bool:
        return self.cache.invalidate(key)

    def cache_clear(self) -> None:
        self.cache.clear()

    @property
    def cache_stats(self) -> dict:
        return self.cache.stats

    # ===================================================================
    # Introspection
    # ===================================================================

    @property
    def routes(self) -> List[dict]:
        """Return a serialisable summary of registered routes."""
        return [
            {
                "method": r.method.value,
                "path": r.path,
                "require_auth": r.require_auth,
                "required_permission": r.required_permission,
                "cache_ttl": r.cache_ttl,
                "description": r.description,
            }
            for r in self._routes
        ]

    # ===================================================================
    # Private helpers
    # ===================================================================

    def _find_route(self, method: HTTPMethod, path: str) -> Optional[_Route]:
        """Exact-match route lookup."""
        with self._lock:
            for r in self._routes:
                if r.method == method and r.path == path:
                    return r
        return None

    def _verify_token(self, token: str) -> bool:
        """Verify that a token is non-expired by checking a permission check."""
        # AuthManager exposes check_permission which validates token expiry.
        # We use a dummy permission check; if it returns False because the token
        # is expired/missing, we treat that as invalid.
        # For a lightweight existence-check we can call check_permission with a
        # permission that every role has ("read").
        return self.auth.check_permission(token, "read")

    @staticmethod
    def _wrap(mw: MiddlewareFn, next_fn: Callable[[], Response], request: Request) -> Callable[[], Response]:
        """Wrap *next_fn* inside *mw* without late-binding issues."""
        def bound():
            return mw(request, next_fn)
        return bound

    def _logging_middleware(self, request: Request, call_next: Callable[[], Response]) -> Response:
        start = time.monotonic()
        resp = call_next()
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s -> %d %.1fms%s",
            request.method.value,
            request.path,
            resp.status_code,
            elapsed_ms,
            " [cached]" if resp.cached else "",
        )
        return resp


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_gateway(**kwargs) -> APIGateway:
    """Return a fresh APIGateway with sensible defaults."""
    return APIGateway(**kwargs)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    gw = create_gateway()

    # --- define a couple of handlers ---
    def list_tools(req: Request) -> Response:
        return Response(body={"tools": ["search", "safety_check", "memory_read"]})

    def run_tool(req: Request) -> Result:
        tool = (req.body or {}).get("tool")
        if not tool:
            return Result.fail("missing tool name")
        return Result.success({"tool": tool, "status": "ok"})

    # --- register routes ---
    gw.route("GET", "/v1/tools", list_tools, cache_ttl=60, description="List available tools")
    gw.route("POST", "/v1/tools/run", run_tool, required_permission="write", description="Run a tool")

    # --- test unauthenticated (should 401) ---
    r1 = gw.handle(Request(method=HTTPMethod.GET, path="/v1/tools"))
    print("GET /v1/tools (no auth):", r1.status_code, r1.body)

    # --- authenticate & retry ---
    # Note: This creates a test user in the auth DB
    try:
        gw.auth.create_user("test_admin", "secret123", "admin")
    except Exception:
        pass  # user already exists from prior run
    token = gw.authenticate("test_admin", "secret123")
    print("Token:", token)

    r2 = gw.handle(Request(method=HTTPMethod.GET, path="/v1/tools", headers={"Authorization": f"Bearer {token}"}))
    print("GET /v1/tools (authed):", r2.status_code, r2.body, r2.cached)

    # --- cache hit ---
    r3 = gw.handle(Request(method=HTTPMethod.GET, path="/v1/tools", headers={"Authorization": f"Bearer {token}"}))
    print("GET /v1/tools (cached):", r3.status_code, r3.cached)

    # --- POST with permission ---
    r4 = gw.handle(Request(
        method=HTTPMethod.POST, path="/v1/tools/run",
        headers={"Authorization": f"Bearer {token}"},
        body={"tool": "search"},
    ))
    print("POST /v1/tools/run:", r4.status_code, r4.body)

    # --- rate limit stress ---
    limited = RateLimiter(max_requests=3, window_seconds=10)
    gw_limited = create_gateway(rate_limiter=limited)
    gw_limited.route("GET", "/ping", lambda req: Response(body="pong"), require_auth=False)
    for i in range(5):
        resp = gw_limited.handle(Request(method=HTTPMethod.GET, path="/ping"))
        print(f"Ping {i+1}: {resp.status_code}")

    print("\nCache stats:", gw.cache_stats)
    print("Registered routes:", json.dumps(gw.routes, indent=2))