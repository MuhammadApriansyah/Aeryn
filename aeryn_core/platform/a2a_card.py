"""A2A Protocol — AgentCard ekspor + agent-to-agent discovery (SUBAGENT-3).

A2A (Agent-to-Agent, Linux Foundation / Google-led): protokol agent ↔ agent.
- AgentCard: metadata discovery (name, skills, capabilities, endpoint)
- .well-known/agent.json: standar discovery path
- skills[]: daftar kemampuan dengan schema input/output

Sumber: a2a-protocol.org/latest, Google A2A announcement (Apr 2025),
Tyk enterprise guide (AgentCard.securitySchemes + skills).

Real data only — no test doubles: skills dari tool registry nyata.
"""

import json
import time
from typing import Dict, Any, List

from aeryn_core.tools import get_tool_registry

# Identitas Aeryn (produksi)
AGENT_IDENTITY = {
    "name": "Aeryn",
    "description": (
        "AI Agent Personal Assistant Daily Worker SaaS Platform — serbabisa, "
        "Daily/Weekly/Monthly. Partner eksekutor + problem solver yang "
        "mengerjakan dan membantu apapun: chat, catat, reminder, briefing, "
        "ledger keuangan, deploy, CI/CD, research, multi-agent orchestration."
    ),
    "version": "62.22",
    "provider": {"organization": "Aeryn Team", "url": "https://github.com/MuhammadApriansyah/Aeryn.git"},
}

# Skills yang diekspor (dari tool registry nyata — nama + deskripsi)
A2A_SKILL_MAP = [
    ("aeryn-chat", "AerynCoreAgent", "Chat natural language dengan trust layer + memory (catat, recall, persona)"),
    ("aeryn-reminder", "AerynCoreAgent", "Reminder multi-schedule: 'besok 7, lusa jam 10' → ZSET + delivery (Discord/termux)"),
    ("aeryn-briefing", "AerynCoreAgent", "Briefing pagi otomatis: jadwal + goals + keuangan + catatan (cron 07:00)"),
    ("aeryn-ledger", "AerynCoreAgent", "Ledger keuangan Rust native: pengeluaran/penghasilan → saldo → laporan bulanan"),
    ("aeryn-memory", "AerynCoreAgent", "Memory bitemporal: facts valid/tx time + vault 5 layer + graph nerve + decay"),
    ("aeryn-research", "AerynCoreAgent", "Research web + reasoning: web_search/read + hybrid retrieval + citation"),
    ("aeryn-orchestrate", "AerynCoreAgent", "Multi-agent orchestration: supervisor loop (decompose → fan-out → sintesis)"),
    ("aeryn-subagent", "AerynCoreAgent", "Subagent spawn: isolated context + tool budget + parallel fan-out"),
]


def build_agent_card(base_url: str = "") -> Dict[str, Any]:
    """AgentCard A2A — dari tool registry nyata (15 tools) + skill map."""
    registry = get_tool_registry()
    tools = registry.list_tools()

    card = {
        "name": AGENT_IDENTITY["name"],
        "description": AGENT_IDENTITY["description"],
        "url": base_url,
        "version": AGENT_IDENTITY["version"],
        "provider": AGENT_IDENTITY["provider"],
        "protocolVersion": "0.3.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": True,
            "stateTransitionHistory": True,
        },
        "defaultInputModes": ["text", "application/json"],
        "defaultOutputModes": ["text", "application/json"],
        "skills": [],
        "tools": [
            {"name": t.name, "description": t.description[:200]}
            for t in tools
        ],
    }
    for name, tag, desc in A2A_SKILL_MAP:
        card["skills"].append({
            "id": name,
            "name": tag,
            "description": desc,
            "tags": [tag, "aeryn"],
        })
    return card


def write_well_known(path: str, base_url: str = "") -> str:
    """Tulis .well-known/agent.json (standar A2A discovery path)."""
    import os
    card = build_agent_card(base_url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    return path
