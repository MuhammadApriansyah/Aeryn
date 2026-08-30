#!/usr/bin/env python3
"""Performance Monitor — Track API performance metrics."""
import time
import threading
from typing import Dict, List

class PerformanceMonitor:
    def __init__(self):
        self._metrics = []
        self._active = False
    
    def start(self):
        self._active = True
    
    def stop(self):
        self._active = False
    
    def record_request(self, path: str, method: str, duration_ms: int, status_code: int):
        self._metrics.append({
            "time": time.time(),
            "path": path,
            "method": method,
            "duration_ms": duration_ms,
            "status": status_code,
        })
        # Keep only last 1000 metrics
        if len(self._metrics) > 1000:
            self._metrics = self._metrics[-1000:]
    
    def get_stats(self) -> Dict:
        if not self._metrics:
            return {"total": 0, "avg_ms": 0, "p95_ms": 0, "error_rate": 0}
        
        durations = [m["duration_ms"] for m in self._metrics]
        errors = sum(1 for m in self._metrics if m["status"] >= 400)
        
        return {
            "total": len(self._metrics),
            "avg_ms": sum(durations) / len(durations),
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "error_rate": errors / len(self._metrics) * 100,
        }
    
    def get_slow_endpoints(self, threshold_ms: int = 100) -> List[Dict]:
        slow = [m for m in self._metrics if m["duration_ms"] > threshold_ms]
        return sorted(slow, key=lambda x: x["duration_ms"], reverse=True)[:10]
    
    def clear(self):
        self._metrics = []

performance_monitor = PerformanceMonitor()

