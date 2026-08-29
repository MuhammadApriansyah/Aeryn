"""V39.16 — Adapters: composable capability modules (Granite Libraries style).

Each adapter is a self-contained capability that can be loaded on demand.
Adapters declare their name, triggers, and behavior contract.
"""
import os
import json
import time
from typing import Optional

from aeryn_core.config import ADAPTERS_DIR


class Adapter:
    """Base class for composable capability modules."""
    
    name: str = ""
    triggers: list = []  # keywords that activate this adapter
    description: str = ""
    
    def can_handle(self, goal: str) -> bool:
        if not goal:
            return False
        g = goal.lower()
        return any(t.lower() in g for t in self.triggers)
    
    def execute(self, goal: str, context: dict) -> Optional[str]:
        """Run the adapter. Returns behavior contract to inject into system prompt."""
        raise NotImplementedError


class CodeReviewAdapter(Adapter):
    name = "code_review"
    triggers = ["review code", "code review", "tinjau kode", "periksa kode", "check code", "review"]
    description = "Code review: check security, quality, best practices"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## CODE REVIEW MODE\n"
            "1. Baca kode dengan teliti\n"
            "2. Cek: security (XSS, injection, auth), performance, readability\n"
            "3. Berikan severity: critical / warning / info\n"
            "4. Suggest fix per issue\n"
            "5. Bahasa: Indonesia\n"
        )


class ResearchAdapter(Adapter):
    name = "research"
    triggers = ["riset", "research", "cari tahu", "investigasi", "deep dive"]
    description = "Research mode: systematic info gathering with citations"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## RESEARCH MODE\n"
            "1. Gunakan web_search untuk kunci utama\n"
            "2. web_read sumber terpercaya\n"
            "3. Cross-reference minimal 2 sumber\n"
            "4. Sajikan dengan struktur: Ringkasan → Detail → Sumber\n"
            "5. Sebutkan sumber secara natural\n"
            "6. Jangan mengarang fakta\n"
        )


class DebugAdapter(Adapter):
    name = "debug"
    triggers = ["debug", "error", "fix", "bug", "perbaiki", "solusi"]
    description = "Debug mode: systematic error diagnosis"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## DEBUG MODE\n"
            "1. Baca error message lengkap\n"
            "2. Gunakan pitfall_search dulu (cek historical errors)\n"
            "3. Identifikasi root cause\n"
            "4. Test hipotesis sebelum solusi\n"
            "5. Berikan fix + penjelasan kenapa\n"
            "6. Minimal 2 alternatif solusi jika ada\n"
        )


class CommitmentTrackerAdapter(Adapter):
    name = "commitment_tracker"
    triggers = ["janji", "commitment", "nanti", "besok", "deadline", "target"]
    description = "Track and remind commitments"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## COMMITMENT TRACKING MODE\n"
            "1. Identifikasi janji/komitmen baru dari user\n"
            "2. Catat ke social memory (add_fact)\n"
            "3. Set reminder mental — akan diingatkan\n"
            "4. Konfirmasi: 'Dicatet! Gue ngingetin ya ~'\n"
        )


class ExplainAdapter(Adapter):
    name = "explain"
    triggers = ["jelaskan", "apa itu", "how to", "cara kerja", "explain", "apa fungsi"]
    description = "Explanation mode: clear, structured explanations"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## EXPLANATION MODE\n"
            "1. Identifikasi level user (pemula/menengah/ahli)\n"
            "2. Struktur: Definisi → Cara Kerja → Contoh → Analogi\n"
            "3. Gunakan bahasa sederhana dulu, tambah detail jika diminta\n"
            "4. Akhiri dengan: 'Ada yang mau ditanya lagi?'\n"
        )


class ToolExecutionAdapter(Adapter):
    name = "tool"
    triggers = ["jalankan", "execute", "run", "baca", "cek", "check", "install", "build", "test", "deploy", "status", "command"]
    description = "Tool execution: shell commands, file ops, system checks"
    
    def execute(self, goal: str, context: dict) -> str:
        return (
            "## TOOL EXECUTION MODE\n"
            "1. Identify command type (shell/file/system)\n"
            "2. Validate safety (no rm -rf, no sandbox escape)\n"
            "3. Execute via terminal tool\n"
            "4. Return structured output\n"
        )


# Registry
_ADAPTERS = [
    CodeReviewAdapter(),
    ResearchAdapter(),
    DebugAdapter(),
    CommitmentTrackerAdapter(),
    ExplainAdapter(),
    ToolExecutionAdapter(),
]


def get_active_adapter(goal: str) -> Optional[Adapter]:
    """Find adapter that matches the goal."""
    for adapter in sorted(_ADAPTERS, key=lambda a: -len(a.triggers)):
        if adapter.can_handle(goal):
            return adapter
    return None


def render_adapter_context(goal: str) -> str:
    """Render adapter behavior contract into system prompt format."""
    adapter = get_active_adapter(goal)
    if adapter:
        return adapter.execute(goal, {})
    return ""


def list_adapters() -> list:
    """List all registered adapters."""
    return [{"name": a.name, "triggers": a.triggers, "description": a.description}
            for a in _ADAPTERS]


def register_adapter(adapter: Adapter):
    """Register a new adapter (dynamic capability extension)."""
    _ADAPTERS.append(adapter)
