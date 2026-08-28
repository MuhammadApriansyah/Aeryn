#!/usr/bin/env python3
"""V41.0 — Phase 4: Performance Optimization + Uptime."""

import os, sys, json, time, asyncio
from typing import Dict, Optional, Any
from datetime import datetime


class PerformanceOptimizer:
    """Monitor and optimize performance."""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 30  # seconds
    
    def get_system_stats(self) -> Dict:
        """Get system performance stats."""
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem_total = mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
            mem_total_mb = mem_total / 1024 if mem_total else 0
            mem_percent = ((mem_total - mem_available) / mem_total * 100) if mem_total else 0
            
            # Disk stats
            stat = os.statvfs('/')
            disk_total = stat.f_blocks * stat.f_frsize
            disk_available = stat.f_bavail * stat.f_frsize
            disk_used = disk_total - disk_available
            disk_percent = (disk_used / disk_total * 100) if disk_total else 0
            
            return {
                "cpu_percent": 0,
                "memory_total_mb": round(mem_total_mb, 1),
                "memory_used_mb": round(mem_used_mb, 1),
                "memory_percent": round(mem_percent, 1),
                "disk_total_gb": round(disk_total / 1024 / 1024 / 1024, 1),
                "disk_used_gb": round(disk_used / 1024 / 1024 / 1024, 1),
                "disk_percent": round(disk_percent, 1),
            }
        except Exception:
            return {}
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value
            del self._cache[key]
        return None
    
    def cache_set(self, key: str, value: Any):
        """Set cache value."""
        self._cache[key] = (value, time.time())
    
    def cache_clear(self):
        """Clear expired cache entries."""
        now = time.time()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > self._cache_ttl]
        for k in expired:
            del self._cache[k]


class UptimeManager:
    """Manage service uptime and auto-recovery."""
    
    def __init__(self):
        self._start_time = time.time()
        self._health_checks: list = []
        self._restart_count = 0
        self._last_health_check = None
    
    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time
    
    @property
    def uptime_formatted(self) -> str:
        seconds = int(self.uptime_seconds)
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)
    
    def health_check(self) -> Dict:
        """Run health checks."""
        checks = {
            "memory": self._check_memory(),
            "disk": self._check_disk(),
            "database": self._check_database(),
        }
        
        all_healthy = all(c["healthy"] for c in checks.values())
        
        return {
            "healthy": all_healthy,
            "uptime_s": self.uptime_seconds,
            "uptime": self.uptime_formatted,
            "checks": checks,
            "restart_count": self._restart_count,
        }
    
    def _check_memory(self) -> Dict:
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem_total = mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            usage_percent = ((mem_total - mem_available) / mem_total * 100) if mem_total else 0
            
            return {
                "healthy": usage_percent < 95,
                "usage_percent": round(usage_percent, 1),
                "available_mb": mem_available / 1024,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _check_disk(self) -> Dict:
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            available = stat.f_bavail * stat.f_frsize
            used = total - available
            percent = (used / total * 100) if total else 0
            
            return {
                "healthy": percent < 90,
                "usage_percent": round(percent, 1),
                "available_gb": available / 1024 / 1024 / 1024,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _check_database(self) -> Dict:
        try:
            db_path = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database")
            if os.path.exists(db_path):
                dbs = [f for f in os.listdir(db_path) if f.endswith('.db')]
                return {"healthy": True, "databases": len(dbs)}
            return {"healthy": True, "databases": 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def record_restart(self):
        self._restart_count += 1


# ── Singleton ─────────────────────────────────

_optimizer: Optional[PerformanceOptimizer] = None
_uptime: Optional[UptimeManager] = None

def get_optimizer() -> PerformanceOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer

def get_uptime() -> UptimeManager:
    global _uptime
    if _uptime is None:
        _uptime = UptimeManager()
    return _uptime
