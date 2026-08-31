#!/usr/bin/env python3
"""V61.1 — Phase-Gated Workflow (8-phase pattern) for Aeryn.

WorkflowStep: a single step with validation.
Checkpoint: requires user approval before proceeding.
Workflow: sequence of steps with state machine.
"""
import os
import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkflowStep:
    """A single step in a workflow with validation."""

    def __init__(self, name: str, description: str,
                 action: Callable = None, validator: Callable = None,
                 requires_approval: bool = False):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.description = description
        self.action = action
        self.validator = validator
        self.requires_approval = requires_approval
        self.status = StepStatus.PENDING
        self.output = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def execute(self, context: Dict = None) -> bool:
        """Execute the step action."""
        self.status = StepStatus.IN_PROGRESS
        self.start_time = time.time()
        try:
            if self.action:
                self.output = self.action(context or {})
            self.end_time = time.time()
            self.status = StepStatus.COMPLETED
            return True
        except Exception as e:
            self.end_time = time.time()
            self.error = str(e)
            self.status = StepStatus.FAILED
            logger.error(f"Step {self.name} failed: {e}")
            return False

    def validate(self) -> bool:
        """Validate step output."""
        if not self.validator:
            return True
        try:
            return self.validator(self.output)
        except Exception as e:
            self.error = str(e)
            return False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "output": str(self.output)[:200] if self.output else None,
            "error": self.error,
            "duration_ms": int((self.end_time - self.start_time) * 1000) if self.end_time and self.start_time else 0,
        }


class Checkpoint:
    """Requires user approval before proceeding."""

    def __init__(self, message: str, options: List[str] = None):
        self.id = str(uuid.uuid4())[:12]
        self.message = message
        self.options = options or ["approve", "reject"]
        self.approved = None
        self.selected_option = None

    def approve(self, option: str = "approve"):
        self.approved = True
        self.selected_option = option

    def reject(self):
        self.approved = False
        self.selected_option = "reject"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "message": self.message,
            "options": self.options,
            "approved": self.approved,
        }


class Workflow:
    """A sequence of steps with state machine."""

    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.current_step_idx = 0
        self.context: Dict[str, Any] = {}
        self.status = "pending"
        self.start_time = None
        self.end_time = None

    def add_step(self, step: WorkflowStep) -> 'Workflow':
        self.steps.append(step)
        return self

    def add_checkpoint(self, after_step: str, checkpoint: Checkpoint):
        self.checkpoints[after_step] = checkpoint

    def get_current_step(self) -> Optional[WorkflowStep]:
        if 0 <= self.current_step_idx < len(self.steps):
            return self.steps[self.current_step_idx]
        return None

    def execute_next(self) -> Optional[Dict]:
        """Execute the next step."""
        step = self.get_current_step()
        if not step:
            return None

        # Check if there's a checkpoint before this step
        checkpoint = self.checkpoints.get(step.name)
        if checkpoint and checkpoint.approved is None:
            return {"status": "waiting_approval", "checkpoint": checkpoint.to_dict()}

        # Execute step
        success = step.execute(self.context)
        if success:
            self.context[step.name] = step.output
            self.current_step_idx += 1
            if self.current_step_idx >= len(self.steps):
                self.status = "completed"
                self.end_time = time.time()
            return {"status": "step_completed", "step": step.to_dict()}
        else:
            return {"status": "step_failed", "step": step.to_dict()}

    def approve_checkpoint(self, step_name: str, option: str = "approve"):
        """Approve a checkpoint."""
        checkpoint = self.checkpoints.get(step_name)
        if checkpoint:
            checkpoint.approve(option)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "current_step": self.current_step_idx,
            "total_steps": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
        }


class SaaSWorkflowBuilder:
    """Builder for 8-phase SaaS startup workflow."""

    @staticmethod
    def build_saas_workflow(idea: str) -> Workflow:
        """Build an 8-phase SaaS workflow."""
        wf = Workflow("SaaS Builder", f"Build SaaS from idea: {idea[:50]}")

        # Phase 1: Research
        wf.add_step(WorkflowStep(
            "research", f"Research market for: {idea}",
            action=lambda ctx: f"Market research for: {idea}",
            requires_approval=True
        ))

        # Phase 2: Design
        wf.add_step(WorkflowStep(
            "design", "Design system architecture",
            action=lambda ctx: "Architecture design document"
        ))

        # Phase 3: Schema
        wf.add_step(WorkflowStep(
            "schema", "Design database schema",
            action=lambda ctx: "Database schema"
        ))

        # Phase 4: Backend
        wf.add_step(WorkflowStep(
            "backend", "Build backend API",
            action=lambda ctx: "Backend API code",
            requires_approval=True
        ))

        # Phase 5: Frontend
        wf.add_step(WorkflowStep(
            "frontend", "Build frontend UI",
            action=lambda ctx: "Frontend code"
        ))

        # Phase 6: Integration
        wf.add_step(WorkflowStep(
            "integration", "Integrate frontend + backend",
            action=lambda ctx: "Integration tests"
        ))

        # Phase 7: Security
        wf.add_step(WorkflowStep(
            "security", "Security audit",
            action=lambda ctx: "Security audit report",
            requires_approval=True
        ))

        # Phase 8: Deploy
        wf.add_step(WorkflowStep(
            "deploy", "Deploy to production",
            action=lambda ctx: "Deployment complete"
        ))

        # Add checkpoints after key phases
        wf.add_checkpoint("research", Checkpoint("Approve research findings?"))
        wf.add_checkpoint("backend", Checkpoint("Approve backend architecture?"))
        wf.add_checkpoint("security", Checkpoint("Approve security audit?"))

        return wf


# Singleton
_workflows: Dict[str, Workflow] = {}

def create_workflow(name: str, idea: str = "") -> Workflow:
    if name == "saas":
        wf = SaaSWorkflowBuilder.build_saas_workflow(idea)
    else:
        wf = Workflow(name)
    _workflows[wf.id] = wf
    return wf

def get_workflow(wf_id: str) -> Optional[Workflow]:
    return _workflows.get(wf_id)

def list_workflows() -> List[Dict]:
    return [{"id": w.id, "name": w.name, "status": w.status} for w in _workflows.values()]
