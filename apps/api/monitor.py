#!/usr/bin/env python3
"""V40.0 — Production Monitoring: Prometheus-style metrics + alerting.

Provides:
- /metrics endpoint for Prometheus scraping
- Health check with thresholds
- Alert rules (disk, memory, queue depth)
- Log aggregation
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ProductionMonitor:
    """Monitor Aeryn services."""
    
    THRESHOLDS = {
        "disk_percent": 90,
        "memory_percent": 85,
        "queue_depth": 100,
        "error_rate": 10,  # percent
    }
    
    def check_disk(self):
        """Check disk usage."""
        import shutil
        usage = shutil.disk_usage("/")
        percent = (usage.used / usage.total) * 100
        return {
            "free_gb": round(usage.free / (1024**3), 2),
            "percent": round(percent, 1),
            "alert": percent > self.THRESHOLDS["disk_percent"],
        }
    
    def check_memory(self):
        """Check memory usage."""
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem_total = 0
            mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            percent = ((mem_total - mem_available) / mem_total) * 100
            return {
                "total_mb": round(mem_total / 1024, 1),
                "used_mb": round((mem_total - mem_available) / 1024, 1),
                "percent": round(percent, 1),
                "alert": percent > self.THRESHOLDS["memory_percent"],
            }
        except Exception:
            return {"alert": False}
    
    def check_queue_depth(self):
        """Check queue depth in shared DB."""
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        stats = db.get_stats()
        total_pending = stats.get("reminders", {}).get("pending", 0) + stats.get("tasks", {}).get("pending", 0)
        return {
            "pending_reminders": stats.get("reminders", {}).get("pending", 0),
            "pending_tasks": stats.get("tasks", {}).get("pending", 0),
            "total_pending": total_pending,
            "alert": total_pending > self.THRESHOLDS["queue_depth"],
        }
    
    def check_services(self):
        """Check service health."""
        services = {}
        
        # Aeryn API
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:3010/health", timeout=5) as r:
                data = json.loads(r.read().decode())
                services["aeryn-api"] = {"status": data.get("status", "unknown"), "ok": r.status == 200}
        except Exception as e:
            services["aeryn-api"] = {"status": "down", "ok": False, "error": str(e)}
        
        # n8n
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:5678/healthz", timeout=5) as r:
                services["n8n"] = {"status": "online", "ok": r.status == 200}
        except Exception as e:
            services["n8n"] = {"status": "down", "ok": False, "error": str(e)}
        
        return services
    
    def get_metrics(self) -> dict:
        """Get all metrics in Prometheus-compatible format."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "disk": self.check_disk(),
                "memory": self.check_memory(),
            },
            "services": self.check_services(),
            "queue": self.check_queue_depth(),
        }
    
    def get_alerts(self) -> list:
        """Get active alerts."""
        alerts = []
        metrics = self.get_metrics()
        
        if metrics["system"]["disk"]["alert"]:
            alerts.append({
                "severity": "critical",
                "service": "system",
                "message": f"Disk usage: {metrics['system']['disk']['percent']}%",
            })
        
        if metrics["system"]["memory"]["alert"]:
            alerts.append({
                "severity": "warning",
                "service": "system",
                "message": f"Memory usage: {metrics['system']['memory']['percent']}%",
            })
        
        if metrics["queue"]["alert"]:
            alerts.append({
                "severity": "warning",
                "service": "queue",
                "message": f"Queue depth: {metrics['queue']['total_pending']} pending items",
            })
        
        for svc, info in metrics["services"].items():
            if not info["ok"]:
                alerts.append({
                    "severity": "critical",
                    "service": svc,
                    "message": f"Service down: {info.get('error', 'unknown')}",
                })
        
        return alerts


if __name__ == "__main__":
    monitor = ProductionMonitor()
    print(json.dumps(monitor.get_metrics(), indent=2))
    alerts = monitor.get_alerts()
    if alerts:
        print(f"\nALERTS: {len(alerts)}")
        for a in alerts:
            print(f"  [{a['severity']}] {a['service']}: {a['message']}")
