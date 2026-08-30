#!/usr/bin/env python3
"""Deployment Dashboard — Monitor deployment status."""
import os, json, time
from typing import Dict, List

class DeployDashboard:
    def __init__(self):
        self._deployments = []
    
    def start_deployment(self, name: str, target: str) -> Dict:
        deploy = {
            "id": len(self._deployments) + 1,
            "name": name,
            "target": target,
            "status": "deploying",
            "started_at": time.time(),
            "completed_at": None,
            "logs": [],
        }
        self._deployments.append(deploy)
        return deploy
    
    def update_status(self, deploy_id: int, status: str, log: str = ""):
        for d in self._deployments:
            if d["id"] == deploy_id:
                d["status"] = status
                if log:
                    d["logs"].append({"time": time.time(), "message": log})
                if status in ("success", "failed"):
                    d["completed_at"] = time.time()
                return True
        return False
    
    def get_deployments(self) -> List[Dict]:
        return self._deployments
    
    def get_active(self) -> List[Dict]:
        return [d for d in self._deployments if d["status"] not in ("success", "failed")]

deploy_dashboard = DeployDashboard()

