#!/usr/bin/env python3
"""
V42.0 — Tool Permission Limits.
Reduce blast radius from successful prompt injection.
"""

import re
from typing import Dict, List, Optional, Set
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Tool risk classification
TOOL_RISKS: Dict[str, RiskLevel] = {
    # Low risk - read-only
    "search": RiskLevel.LOW,
    "read_file": RiskLevel.LOW,
    "list_files": RiskLevel.LOW,
    "get_time": RiskLevel.LOW,
    
    # Medium risk - limited write
    "write_file": RiskLevel.MEDIUM,
    "edit_file": RiskLevel.MEDIUM,
    "create_note": RiskLevel.MEDIUM,
    
    # High risk - external communication
    "send_email": RiskLevel.HIGH,
    "send_message": RiskLevel.HIGH,
    "webhook": RiskLevel.HIGH,
    
    # Critical risk - system access
    "execute_command": RiskLevel.CRITICAL,
    "shell": RiskLevel.CRITICAL,
    "database_write": RiskLevel.CRITICAL,
    "admin_action": RiskLevel.CRITICAL,
}

# High-stakes patterns requiring confirmation
HIGH_STAKES_PATTERNS = [
    r'(?:delete|remove|drop)\s+(?:from|database|table|file)',
    r'(?:send|email|message)\s+(?:to|all)',
    r'(?:transfer|payment|charge)\s+(?:money|fund|amount)',
    r'(?:execute|run|invoke)\s+(?:command|script|shell)',
    r'(?:modify|change|update)\s+(?:config|settings|permissions)',
]

COMPILED_HIGH_STAKES = [re.compile(p, re.IGNORECASE) for p in HIGH_STAKES_PATTERNS]


def get_tool_risk(tool_name: str) -> RiskLevel:
    """Get risk level for a tool."""
    return TOOL_RISKS.get(tool_name.lower(), RiskLevel.MEDIUM)


def requires_confirmation(tool_name: str, args: str = "") -> bool:
    """Check if tool execution requires user confirmation."""
    risk = get_tool_risk(tool_name)
    
    # Critical tools always require confirmation
    if risk == RiskLevel.CRITICAL:
        return True
    
    # High risk tools require confirmation
    if risk == RiskLevel.HIGH:
        return True
    
    # Check for high-stakes patterns in args
    for pattern in COMPILED_HIGH_STAKES:
        if pattern.search(args):
            return True
    
    return False


def get_allowed_tools(session_risk_level: RiskLevel) -> Set[str]:
    """Get tools allowed for a given session risk level."""
    allowed = set()
    for tool, risk in TOOL_RISKS.items():
        if risk.value <= session_risk_level.value:
            allowed.add(tool)
    return allowed


def validate_tool_call(tool_name: str, args: str, session_risk: RiskLevel = RiskLevel.MEDIUM) -> tuple:
    """
    Validate if a tool call is allowed.
    
    Returns:
        Tuple of (is_allowed, reason)
    """
    # Check if tool is allowed for session risk level
    allowed_tools = get_allowed_tools(session_risk)
    if tool_name.lower() not in allowed_tools:
        return False, f"Tool '{tool_name}' not allowed for risk level {session_risk.value}"
    
    # Check if confirmation required
    if requires_confirmation(tool_name, args):
        return False, "Confirmation required for this action"
    
    return True, ""
