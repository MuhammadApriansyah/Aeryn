#!/usr/bin/env python3
"""V61.1 — Multi-Agent Orchestration (crewAI-style) for Aeryn.

Crew: group of agents working toward a shared goal.
Agent: specialized role with backstory, goals, tools.
Task: assigned work with expected output.
Process: sequential or hierarchical execution.
"""
import os
import sys
import json
import time
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    CREATIVE = "creative"
    PSYCH = "psych"
    REASONING = "reasoning"
    GOV = "gov"
    INFRA = "infra"


class Agent:
    """A specialized agent with role, backstory, and tools."""

    def __init__(self, name: str, role: AgentRole, backstory: str,
                 goal: str, tools: List[str] = None, llm_client=None):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.role = role
        self.backstory = backstory
        self.goal = goal
        self.tools = tools or []
        self.llm_client = llm_client
        self.status = "idle"
        self.results: List[Dict] = []

    async def execute(self, task: 'Task', context: Dict = None) -> Dict:
        """Execute a task using LLM + tools."""
        self.status = "working"
        try:
            # Build system prompt from backstory + goal
            system_prompt = f"{self.backstory}\n\nYour Goal: {self.goal}\n"
            if self.tools:
                system_prompt += f"Available Tools: {', '.join(self.tools)}\n"
            if context:
                system_prompt += f"\nContext: {json.dumps(context, ensure_ascii=False)[:1000]}"

            # Call LLM
            from aeryn_core.utils.llm_client import get_mode_router
            router = get_mode_router()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task.description},
            ]
            
            result = await router.llm.chat(messages)
            output = result.get("content", "")
            
            task.completed = True
            task.output = output
            self.status = "done"
            
            return {
                "agent": self.name,
                "role": self.role.value,
                "task": task.name,
                "output": output,
                "status": "completed",
            }
        except Exception as e:
            self.status = "error"
            return {
                "agent": self.name,
                "role": self.role.value,
                "task": task.name,
                "error": str(e),
                "status": "failed",
            }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "backstory": self.backstory[:100],
            "goal": self.goal,
            "tools": self.tools,
            "status": self.status,
        }


class Task:
    """A unit of work assigned to an agent."""

    def __init__(self, name: str, description: str, expected_output: str = "",
                 agent: Agent = None, context: Dict = None):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.description = description
        self.expected_output = expected_output
        self.agent = agent
        self.context = context or {}
        self.completed = False
        self.output = None
        self.start_time = None
        self.end_time = None

    async def execute(self) -> Dict:
        if not self.agent:
            return {"error": "No agent assigned"}
        self.start_time = time.time()
        result = await self.agent.execute(self, self.context)
        self.end_time = time.time()
        result["duration_ms"] = int((self.end_time - self.start_time) * 1000) if self.end_time else 0
        return result

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description[:100],
            "agent": self.agent.name if self.agent else None,
            "completed": self.completed,
            "output": self.output[:200] if self.output else None,
        }


class Crew:
    """A group of agents working together on tasks."""

    def __init__(self, name: str, agents: List[Agent] = None,
                 process: str = "sequential"):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.agents: List[Agent] = agents or []
        self.tasks: List[Task] = []
        self.process = process  # "sequential" or "hierarchical"
        self.context: Dict[str, Any] = {}
        self.results: List[Dict] = []

    def add_agent(self, agent: Agent):
        self.agents.append(agent)

    def add_task(self, task: Task):
        self.tasks.append(task)

    async def kickoff(self) -> Dict:
        """Execute all tasks using the specified process."""
        start = time.time()
        self.results = []

        if self.process == "sequential":
            for task in self.tasks:
                result = await task.execute()
                self.results.append(result)
                # Pass output as context to next task
                if task.output:
                    self.context[task.name] = task.output
        elif self.process == "hierarchical":
            # Master agent delegates to sub-agents
            master = self.agents[0] if self.agents else None
            if master:
                for task in self.tasks:
                    task.agent = master
                    result = await task.execute()
                    self.results.append(result)

        duration = int((time.time() - start) * 1000)
        return {
            "crew": self.name,
            "process": self.process,
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "completed": sum(1 for t in self.tasks if t.completed),
            "total_duration_ms": duration,
            "results": self.results,
        }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "agents": [a.to_dict() for a in self.agents],
            "tasks": [t.to_dict() for t in self.tasks],
            "process": self.process,
        }


class DivisionManager:
    """Manages the 5 Aeryn divisions as crews."""

    def __init__(self):
        self._divisions: Dict[str, Crew] = {}
        self._setup_divisions()

    def _setup_divisions(self):
        """Initialize the 5 Aeryn divisions."""
        # Division 1: Creative
        creative = Crew("Creative Division", process="sequential")
        creative.add_agent(Agent(
            "Creative Lead", AgentRole.CREATIVE,
            "You are the Creative Lead. You design, write, and craft content.",
            "Generate creative solutions, designs, and content.",
            tools=["web_search", "web_fetch"]
        ))
        creative.add_agent(Agent(
            "Style Specialist", AgentRole.CREATIVE,
            "You are the Style Specialist. You ensure brand consistency and visual quality.",
            "Review and refine creative output for style and brand alignment.",
            tools=["fs_read", "fs_write"]
        ))
        self._divisions["creative"] = creative

        # Division 2: Psych
        psych = Crew("Psychology Division", process="sequential")
        psych.add_agent(Agent(
            "Analyst", AgentRole.PSYCH,
            "You are the Psychology Analyst. You analyze emotions, behaviors, and sentiments.",
            "Provide deep psychological and behavioral analysis.",
            tools=["memory_search", "web_search"]
        ))
        self._divisions["psych"] = psych

        # Division 3: Reasoning
        reasoning = Crew("Reasoning Division", process="sequential")
        reasoning.add_agent(Agent(
            "Researcher", AgentRole.REASONING,
            "You are the Lead Researcher. You solve complex problems with logic and evidence.",
            "Conduct research, solve problems, and provide evidence-based answers.",
            tools=["web_search", "web_fetch", "memory_search"]
        ))
        reasoning.add_agent(Agent(
            "Code Expert", AgentRole.REASONING,
            "You are the Code Expert. You write, review, and debug code.",
            "Write clean, efficient code and debug issues.",
            tools=["terminal", "fs_read", "fs_write"]
        ))
        self._divisions["reasoning"] = reasoning

        # Division 4: Gov
        gov = Crew("Governance Division", process="sequential")
        gov.add_agent(Agent(
            "Compliance Officer", AgentRole.GOV,
            "You are the Compliance Officer. You ensure security, policy, and legal compliance.",
            "Audit for compliance, security risks, and policy violations.",
            tools=["web_search", "fs_read"]
        ))
        self._divisions["gov"] = gov

        # Division 5: Infra
        infra = Crew("Infrastructure Division", process="sequential")
        infra.add_agent(Agent(
            "DevOps Engineer", AgentRole.INFRA,
            "You are the DevOps Engineer. You deploy, monitor, and scale infrastructure.",
            "Set up deployment, monitoring, and infrastructure automation.",
            tools=["terminal", "fs_read", "fs_write", "web_search"]
        ))
        self._divisions["infra"] = infra

    def get_division(self, name: str) -> Optional[Crew]:
        return self._divisions.get(name.lower())

    def list_divisions(self) -> List[str]:
        return list(self._divisions.keys())

    async def execute_division(self, name: str, tasks: List[Dict]) -> Dict:
        """Execute tasks on a division."""
        division = self.get_division(name)
        if not division:
            return {"error": f"Division not found: {name}"}

        # Clear previous tasks
        division.tasks = []
        division.context = {}

        # Add new tasks
        for task_data in tasks:
            # Assign agent based on task type or round-robin
            agent_idx = len(division.tasks) % len(division.agents) if division.agents else 0
            agent = division.agents[agent_idx] if division.agents else None
            
            task = Task(
                name=task_data.get("name", f"task_{len(division.tasks)}"),
                description=task_data.get("description", ""),
                expected_output=task_data.get("expected_output", ""),
                agent=agent,
                context=task_data.get("context", {}),
            )
            division.add_task(task)

        return await division.kickoff()

    def get_status(self) -> Dict:
        return {
            "divisions": {
                name: {
                    "agents": len(crew.agents),
                    "pending_tasks": len([t for t in crew.tasks if not t.completed]),
                }
                for name, crew in self._divisions.items()
            }
        }


# Singleton
_manager = None

def get_division_manager() -> DivisionManager:
    global _manager
    if _manager is None:
        _manager = DivisionManager()
    return _manager
