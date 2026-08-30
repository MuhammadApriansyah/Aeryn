#!/usr/bin/env python3
"""Workflow DSL — Define custom generation workflows."""
import json
import time
from typing import Dict, List, Any

class WorkflowStep:
    def __init__(self, name: str, action: str, params: Dict = None):
        self.name = name
        self.action = action
        self.params = params or {}
        self.status = "pending"
        self.result = None
        self.error = None
    
    def execute(self, context: Dict) -> Any:
        self.status = "running"
        try:
            from aeryn_core.workflow_dsl.actions import ACTION_MAP
            action_fn = ACTION_MAP.get(self.action)
            if not action_fn:
                raise ValueError(f"Unknown action: {self.action}")
            self.result = action_fn(self.params, context)
            self.status = "completed"
            return self.result
        except Exception as e:
            self.error = str(e)
            self.status = "failed"
            raise

class Workflow:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps = []
        self.context = {}
        self._on_error = "stop"
    
    def add_step(self, name: str, action: str, params: Dict = None):
        self.steps.append(WorkflowStep(name, action, params))
        return self
    
    def on_error(self, handler: str = "stop"):
        self._on_error = handler
        return self
    
    def run(self):
        results = []
        start_time = time.time()
        
        for step in self.steps:
            try:
                result = step.execute(self.context)
                self.context[step.name] = result
                results.append({"step": step.name, "status": "ok"})
            except Exception as e:
                results.append({"step": step.name, "status": "error", "error": str(e)})
                if self._on_error == "stop":
                    break
        
        return {"workflow": self.name, "duration_ms": int((time.time() - start_time) * 1000), "steps": results}
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "on_error": self._on_error,
            "steps": [{"name": s.name, "action": s.action, "params": s.params} for s in self.steps]
        }

class WorkflowDSL:
    def create(self, name: str, description: str = "") -> Workflow:
        return Workflow(name, description)
    
    def load_from_file(self, path: str) -> Workflow:
        with open(path) as f:
            data = json.load(f)
        wf = Workflow(data["name"], data.get("description", ""))
        for s in data.get("steps", []):
            wf.add_step(s["name"], s["action"], s.get("params", {}))
        return wf

workflow_dsl = WorkflowDSL()
