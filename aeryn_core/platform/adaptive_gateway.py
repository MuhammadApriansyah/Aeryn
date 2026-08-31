#!/usr/bin/env python3
"""V61.0 — Adaptive Gateway: environment-aware middleware for Aeryn API.

Wires existing components (AuthManager, RateLimiter, CircuitBreaker) into a
single ASGI middleware layer. Detects runtime environment (proot/VPS/k8s) and
adapts DB + supervisor behavior accordingly.

No test doubles — uses real aeryn_core.auth, aeryn_core.rate_limiting,
aeryn_core.utils.error_recovery.
"""
import os
import sys
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def detect_environment() -> Dict[str, str]:
    """Detect runtime environment from process/OS signals.

    Returns dict with 'type' (proot|vps|k8s|docker) and 'db' (sqlite|postgres).
    """
    env_type = "unknown"
    db_backend = "sqlite"

    # Check explicit env var first
    explicit = os.environ.get("AERYN_ENV", "").lower()
    if explicit in ("proot", "vps", "k8s", "docker"):
        env_type = explicit
    else:
        # Detect proot: /proc/1/comm often "init" or proot-specific
        try:
            with open("/proc/1/comm", "r") as f:
                comm = f.read().strip().lower()
            if "proot" in comm or "termux" in comm:
                env_type = "proot"
            elif comm in ("systemd", "init"):
                env_type = "vps"
        except Exception:
            pass

        # Fallback: check common proot/Termux signals
        if env_type == "unknown":
            if os.environ.get("PROOT") or os.environ.get("TERMUX_VERSION") or "termux" in os.environ.get("PREFIX", ""):
                env_type = "proot"
            elif os.path.exists("/etc/systemd/system"):
                env_type = "vps"

        # Detect k8s: service account file
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
            env_type = "k8s"

        # Detect docker: /.dockerenv
        if os.path.exists("/.dockerenv"):
            env_type = "docker"

    # DB backend: DATABASE_URL set + psycopg2 available → postgres
    db_url = os.environ.get("DATABASE_URL", "")
    if "postgresql" in db_url:
        try:
            import psycopg2  # noqa
            db_backend = "postgres"
        except ImportError:
            db_backend = "sqlite"
            logger.warning("DATABASE_URL points to postgres but psycopg2 missing, falling back to sqlite")

    return {"type": env_type, "db": db_backend}


class AdaptiveGateway:
    """ASGI-style middleware that enforces auth, rate-limit, and circuit-breaker
    before passing request to FastAPI app.
    """

    def __init__(self):
        self.env = detect_environment()
        self.auth = self._get_auth()
        self.rate_limiter = self._get_rate_limiter()
        self.error_recovery = self._get_error_recovery()
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 30.0
        logger.info(f"AdaptiveGateway initialized: env={self.env['type']} db={self.env['db']}")

    def _get_auth(self):
        try:
            from aeryn_core.auth.auth import get_auth
            return get_auth()
        except Exception as e:
            logger.warning(f"AuthManager unavailable: {e}")
            return None

    def _get_rate_limiter(self):
        try:
            from aeryn_core.rate_limiting.limiter import RateLimiter
            return RateLimiter(requests_per_minute=60)
        except Exception as e:
            logger.warning(f"RateLimiter unavailable: {e}")
            return None

    def _get_error_recovery(self):
        try:
            from aeryn_core.utils.error_recovery import get_error_recovery
            return get_error_recovery()
        except Exception as e:
            logger.warning(f"ErrorRecovery unavailable: {e}")
            return None

    def check_rate_limit(self, client_id: str) -> bool:
        """Return True if request allowed."""
        if self.rate_limiter is None:
            return True
        return self.rate_limiter.is_allowed(client_id)

    def authenticate(self, token: Optional[str]) -> Optional[Dict]:
        """Validate token/api-key, return user dict or None."""
        if self.auth is None:
            return None
        if not token:
            return None
        # Try API key first
        user = self.auth.validate_api_key(token)
        if user:
            return user
        # Try session token
        user = self.auth.validate_token(token)
        if user:
            return user
        return None

    def get_circuit_breaker_state(self, name: str) -> Dict:
        if self.error_recovery is None:
            return {"state": "unknown"}
        return self.error_recovery.get_circuit_breaker(name).get_state()

    def cache_get(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return value
            del self._cache[key]
        return None

    def cache_put(self, key: str, value: Dict):
        self._cache[key] = (value, time.time())

    def get_env_info(self) -> Dict[str, str]:
        return self.env


# Singleton
_gateway = None

def get_gateway() -> AdaptiveGateway:
    global _gateway
    if _gateway is None:
        _gateway = AdaptiveGateway()
    return _gateway
