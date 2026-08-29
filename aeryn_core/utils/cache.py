#!/usr/bin/env python3
"""
V41.0 — Caching Layer.
LRU cache untuk mengurangi database queries.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict


class LRUCache:
    """Thread-safe LRU Cache."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl  # seconds
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time())
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
    
    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }


# Global cache instances
_user_cache = LRUCache(max_size=500, ttl=600)  # 10 minutes
_session_cache = LRUCache(max_size=1000, ttl=300)  # 5 minutes
_workspace_cache = LRUCache(max_size=200, ttl=1800)  # 30 minutes


def get_user_cache() -> LRUCache:
    return _user_cache


def get_session_cache() -> LRUCache:
    return _session_cache


def get_workspace_cache() -> LRUCache:
    return _workspace_cache
