"""Multi-Agent System — 5 Cognitive Divisions + Protocol + Orchestration.

Diadaptasi dari:
- OpenMAIC: Multi-agent learning, classroom generation
- Atlas: Agent Communication Protocol, lifecycle management
- DeepSeek Harness: Everything-is-a-plugin, agent skills
- Superpowers: Composable skills, multi-platform
"""

import os
import json
import logging
import importlib
import importlib.util
import asyncio
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """5 Cognitive Divisions of Aeryn."""
    CREATIVE = "creative"
    PSYCH = "psych"
    REASONING = "reasoning"
    GOVERNANCE = "governance"
    INFRA = "infra"


class MessageRole(Enum):
    """Message roles in agent communication."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class AgentMessage:
    """Message in agent communication protocol."""
    id: str
    sender: str
    receiver: str
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        return cls(
            id=data["id"],
            sender=data["sender"],
            receiver=data["receiver"],
            role=MessageRole(data["role"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class AgentTask:
    """Task for an agent to execute."""
    id: str
    agent_id: str
    description: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class AgentProtocol:
    """Agent Communication Protocol (ACP) — diadaptasi dari Atlas.
    
    Standardized messaging between agents with thread-based conversations.
    """
    
    def __init__(self):
        self._threads: Dict[str, List[AgentMessage]] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def create_thread(self, thread_id: str) -> str:
        """Create a new conversation thread."""
        if thread_id not in self._threads:
            self._threads[thread_id] = []
        return thread_id
    
    def send_message(self, thread_id: str, message: AgentMessage):
        """Send a message to a thread."""
        if thread_id not in self._threads:
            self.create_thread(thread_id)
        self._threads[thread_id].append(message)
    
    def get_thread(self, thread_id: str) -> List[AgentMessage]:
        """Get all messages in a thread."""
        return self._threads.get(thread_id, [])
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a message type."""
        self._handlers[message_type] = handler
    
    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle an incoming message."""
        handler = self._handlers.get(message.role.value)
        if handler:
            return handler(message)
        return None
    
    def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history."""
        messages = self._threads.get(thread_id, [])
        return [m.to_dict() for m in messages[-limit:]]


class Agent:
    """Base agent class — diadaptasi dari Atlas agent manager."""
    
    def __init__(self, agent_id: str, name: str, role: AgentRole, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.status = "idle"  # idle, running, stopped, error
        self._tools: Dict[str, Callable] = {}
        self._skills: Dict[str, Any] = {}
        self._protocol = AgentProtocol()
        self._task_history: List[AgentTask] = []
    
    def register_tool(self, name: str, handler: Callable):
        """Register a tool for this agent."""
        self._tools[name] = handler
    
    def register_skill(self, name: str, skill: Any):
        """Register a skill for this agent."""
        self._skills[name] = skill
    
    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute a task."""
        self.status = "running"
        task.status = "running"
        task.started_at = datetime.utcnow()
        
        try:
            # Process task based on role
            result = await self._process_task(task)
            task.outputs = result
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Agent {self.agent_id} failed: {e}")
        finally:
            task.completed_at = datetime.utcnow()
            self.status = "idle"
            self._task_history.append(task)
        
        return task
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a task — override in subclasses."""
        return {"result": f"Processed by {self.name}"}
    
    def get_tools(self) -> List[str]:
        """Get list of registered tools."""
        return list(self._tools.keys())
    
    def get_skills(self) -> List[str]:
        """Get list of registered skills."""
        return list(self._skills.keys())
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get task execution history."""
        return [t.to_dict() for t in self._task_history]


class CreativeAgent(Agent):
    """Creative Division — generates content, ideas, and creative solutions."""
    
    def __init__(self, agent_id: str = "creative_001"):
        super().__init__(
            agent_id=agent_id,
            name="Creative Agent",
            role=AgentRole.CREATIVE,
            description="Generates creative content, ideas, and solutions"
        )
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process creative task."""
        content = task.inputs.get("content", "")
        style = task.inputs.get("style", "creative")
        
        # Simulate creative processing
        return {
            "original": content,
            "creative_output": f"Creative version of: {content}",
            "style": style,
            "variations": [
                f"Variation 1: {content}",
                f"Variation 2: {content}",
                f"Variation 3: {content}",
            ]
        }


class PsychAgent(Agent):
    """Psych Division — analyzes emotions, motivations, and human behavior."""
    
    def __init__(self, agent_id: str = "psych_001"):
        super().__init__(
            agent_id=agent_id,
            name="Psych Agent",
            role=AgentRole.PSYCH,
            description="Analyzes emotions, motivations, and behavior"
        )
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process psych analysis task."""
        text = task.inputs.get("text", "")
        
        # Simulate emotion detection
        return {
            "text": text,
            "emotions": {
                "joy": 0.7,
                "sadness": 0.1,
                "anger": 0.05,
                "fear": 0.05,
                "surprise": 0.1,
            },
            "sentiment": "positive",
            "confidence": 0.85,
        }


class ReasoningAgent(Agent):
    """Reasoning Division — logical analysis, problem solving, critical thinking."""
    
    def __init__(self, agent_id: str = "reasoning_001"):
        super().__init__(
            agent_id=agent_id,
            name="Reasoning Agent",
            role=AgentRole.REASONING,
            description="Logical analysis and problem solving"
        )
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process reasoning task."""
        problem = task.inputs.get("problem", "")
        
        # Simulate reasoning
        return {
            "problem": problem,
            "analysis": f"Analysis of: {problem}",
            "steps": [
                "Step 1: Identify the problem",
                "Step 2: Break down into sub-problems",
                "Step 3: Solve each sub-problem",
                "Step 4: Combine solutions",
            ],
            "conclusion": f"Solution to: {problem}",
            "confidence": 0.92,
        }


class GovernanceAgent(Agent):
    """Governance Division — safety, compliance, ethical oversight."""
    
    def __init__(self, agent_id: str = "gov_001"):
        super().__init__(
            agent_id=agent_id,
            name="Governance Agent",
            role=AgentRole.GOVERNANCE,
            description="Safety, compliance, and ethical oversight"
        )
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process governance check."""
        content = task.inputs.get("content", "")
        
        # Simulate safety check
        return {
            "content": content,
            "safe": True,
            "violations": [],
            "recommendations": [
                "Recommendation 1: Add more context",
                "Recommendation 2: Consider alternative phrasing",
            ],
            "risk_level": "low",
        }


class InfraAgent(Agent):
    """Infrastructure Division — deployment, monitoring, optimization."""
    
    def __init__(self, agent_id: str = "infra_001"):
        super().__init__(
            agent_id=agent_id,
            name="Infra Agent",
            role=AgentRole.INFRA,
            description="Deployment, monitoring, and optimization"
        )
    
    async def _process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process infrastructure task."""
        action = task.inputs.get("action", "status")
        
        return {
            "action": action,
            "status": "success",
            "metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 62.1,
                "disk_usage": 78.3,
                "network_latency": 12.5,
            },
            "recommendations": [
                "Scale up memory",
                "Optimize disk usage",
            ]
        }


class AgentManager:
    """Manages all agents — diadaptasi dari Atlas agent manager."""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._protocol = AgentProtocol()
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize the 5 cognitive divisions."""
        self.register_agent(CreativeAgent())
        self.register_agent(PsychAgent())
        self.register_agent(ReasoningAgent())
        self.register_agent(GovernanceAgent())
        self.register_agent(InfraAgent())
    
    def register_agent(self, agent: Agent):
        """Register an agent."""
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.role.value})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[Agent]:
        """Get all agents with a specific role."""
        return [a for a in self._agents.values() if a.role == role]
    
    def list_agents(self) -> List[Dict[str, str]]:
        """List all agents."""
        return [
            {
                "id": a.agent_id,
                "name": a.name,
                "role": a.role.value,
                "status": a.status,
            }
            for a in self._agents.values()
        ]
    
    async def execute_task(self, agent_id: str, task: AgentTask) -> AgentTask:
        """Execute a task on a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        return await agent.execute(task)
    
    async def execute_parallel(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Execute multiple tasks in parallel."""
        return await asyncio.gather(*[
            self.execute_task(t.agent_id, t) for t in tasks
        ])
    
    async def execute_sequential(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Execute multiple tasks sequentially."""
        results = []
        for task in tasks:
            result = await self.execute_task(task.agent_id, task)
            results.append(result)
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        return {
            "total_agents": len(self._agents),
            "agents_by_role": {
                role.value: len(self.get_agents_by_role(role))
                for role in AgentRole
            },
            "total_tasks": sum(
                len(a.get_task_history()) for a in self._agents.values()
            ),
        }


class MultiAgentOrchestrator:
    """Orchestrates multiple agents — diadaptasi dari OpenMAIC."""
    
    def __init__(self, agent_manager: AgentManager = None):
        self.agent_manager = agent_manager or AgentManager()
        self._workflows: Dict[str, List[AgentTask]] = {}
    
    def create_workflow(self, name: str, tasks: List[AgentTask]):
        """Create a multi-agent workflow."""
        self._workflows[name] = tasks
    
    async def execute_workflow(self, name: str) -> List[AgentTask]:
        """Execute a multi-agent workflow."""
        if name not in self._workflows:
            raise ValueError(f"Workflow not found: {name}")
        
        tasks = self._workflows[name]
        return await self.agent_manager.execute_sequential(tasks)
    
    async def classroom_generation(self, document: str) -> Dict[str, Any]:
        """Generate classroom from document — diadaptasi dari OpenMAIC."""
        # Teacher generates content
        teacher_task = AgentTask(
            id="teacher_001",
            agent_id="creative_001",
            description="Generate course content",
            inputs={"content": document, "style": "educational"},
        )
        teacher_result = await self.agent_manager.execute_task("creative_001", teacher_task)
        
        # Student learns
        student_task = AgentTask(
            id="student_001",
            agent_id="reasoning_001",
            description="Learn from content",
            inputs={"problem": teacher_result.outputs.get("creative_output", "")},
        )
        student_result = await self.agent_manager.execute_task("reasoning_001", student_task)
        
        # Evaluator assesses
        eval_task = AgentTask(
            id="eval_001",
            agent_id="psych_001",
            description="Assess understanding",
            inputs={"text": str(student_result.outputs)},
        )
        eval_result = await self.agent_manager.execute_task("psych_001", eval_task)
        
        return {
            "content": teacher_result.outputs,
            "understanding": student_result.outputs,
            "assessment": eval_result.outputs,
        }
    
    async def collaborative_problem_solving(self, problem: str) -> Dict[str, Any]:
        """Multiple agents collaborate to solve a problem."""
        # Reasoning analyzes
        reasoning_task = AgentTask(
            id="reasoning_001",
            agent_id="reasoning_001",
            description="Analyze problem",
            inputs={"problem": problem},
        )
        
        # Creative generates ideas
        creative_task = AgentTask(
            id="creative_001",
            agent_id="creative_001",
            description="Generate ideas",
            inputs={"content": problem, "style": "brainstorm"},
        )
        
        # Execute in parallel
        results = await self.agent_manager.execute_parallel([
            reasoning_task,
            creative_task,
        ])
        
        # Governance checks
        gov_task = AgentTask(
            id="gov_001",
            agent_id="gov_001",
            description="Safety check",
            inputs={"content": str([r.outputs for r in results])},
        )
        gov_result = await self.agent_manager.execute_task("gov_001", gov_task)
        
        return {
            "analysis": results[0].outputs if len(results) > 0 else {},
            "ideas": results[1].outputs if len(results) > 1 else {},
            "safety": gov_result.outputs,
        }
