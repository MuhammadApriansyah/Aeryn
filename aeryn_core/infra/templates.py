#!/usr/bin/env python3
"""
V44.0 — Agent Templates.
Pre-built agent templates for common use cases.
"""

from typing import Dict, List, Optional


class AgentTemplate:
    """A template for creating agents."""
    
    def __init__(self, name: str, description: str, category: str,
                 system_prompt: str, tools: List[str], config: Dict):
        self.name = name
        self.description = description
        self.category = category
        self.system_prompt = system_prompt
        self.tools = tools
        self.config = config


class TemplateRegistry:
    """Registry of agent templates."""
    
    def __init__(self):
        self._templates: Dict[str, AgentTemplate] = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default templates."""
        self.register(AgentTemplate(
            name="researcher",
            description="Research agent that finds and analyzes information",
            category="productivity",
            system_prompt="""You are a research assistant. Your job is to:
1. Search for information on the given topic
2. Analyze and synthesize findings
3. Present clear, structured summaries
4. Cite sources when possible

Be thorough but concise. Focus on accuracy.""",
            tools=["search", "read_file", "write_file"],
            config={"max_results": 10, "depth": "moderate"}
        ))
        
        self.register(AgentTemplate(
            name="writer",
            description="Writing agent that creates content",
            category="creative",
            system_prompt="""You are a writing assistant. Your job is to:
1. Create engaging, well-structured content
2. Adapt tone to the target audience
3. Follow brand guidelines when provided
4. Suggest improvements iteratively

Be creative but professional. Focus on clarity.""",
            tools=["write_file", "edit_file", "read_file"],
            config={"tone": "professional", "format": "markdown"}
        ))
        
        self.register(AgentTemplate(
            name="coder",
            description="Coding agent that writes and reviews code",
            category="development",
            system_prompt="""You are a coding assistant. Your job is to:
1. Write clean, well-documented code
2. Follow best practices and conventions
3. Review code for bugs and improvements
4. Explain your reasoning clearly

Be precise. Focus on correctness and maintainability.""",
            tools=["write_file", "edit_file", "execute_command", "read_file"],
            config={"language": "python", "test": True}
        ))
        
        self.register(AgentTemplate(
            name="analyst",
            description="Data analysis agent",
            category="analytics",
            system_prompt="""You are a data analyst. Your job is to:
1. Analyze datasets and extract insights
2. Create clear visualizations
3. Explain findings in simple terms
4. Suggest actionable recommendations

Be analytical but accessible. Focus on actionable insights.""",
            tools=["read_file", "write_file", "execute_command"],
            config={"format": "chart", "style": "simple"}
        ))
        
        self.register(AgentTemplate(
            name="support",
            description="Customer support agent",
            category="customer_service",
            system_prompt="""You are a customer support agent. Your job is to:
1. Understand customer issues quickly
2. Provide clear, helpful solutions
3. Escalate when necessary
4. Follow up to ensure satisfaction

Be empathetic and solution-focused.""",
            tools=["search", "read_file", "send_message"],
            config={"tone": "friendly", "max_response_time": 30}
        ))
    
    def register(self, template: AgentTemplate):
        """Register a template."""
        self._templates[template.name] = template
    
    def get(self, name: str) -> Optional[AgentTemplate]:
        """Get a template by name."""
        return self._templates.get(name)
    
    def list_templates(self) -> List[Dict]:
        """List all templates."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "tools": t.tools,
            }
            for t in self._templates.values()
        ]
    
    def list_by_category(self, category: str) -> List[Dict]:
        """List templates by category."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "tools": t.tools,
            }
            for t in self._templates.values()
            if t.category == category
        ]
    
    def get_categories(self) -> List[str]:
        """Get all categories."""
        return list(set(t.category for t in self._templates.values()))


template_registry = TemplateRegistry()
