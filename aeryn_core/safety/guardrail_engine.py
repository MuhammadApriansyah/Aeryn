"""Guardrail System — 4-layer production guardrails.

Berdasarkan riset (Contro1 "12 guardrails", arXiv 2605.24309 "AHI"):
1. Policy — deklarasi aturan di config
2. Tool Permission — least-privilege scope per tool
3. Runtime Validation — check DI DALAM tool sebelum eksekusi
4. Human Approval — approval gate untuk destructive action

Prinsip inti:
- "The tool itself is the gate" — bukan prompt, bukan blocklist string
- "The model's intelligence is not a substitute for a permission boundary"
- "No deployed system trusts an LLM alone for safety"
"""

import json
import os
import hashlib
import sqlite3
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from aeryn_core.utils.config import DATABASE_DIR


# ============================================
# LAPIS 1: POLICY (deklaratif)
# ============================================

class RiskLevel(str, Enum):
    """Risk level of a tool action."""
    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    IRREVERSIBLE = "irreversible"


@dataclass
class ToolPolicy:
    """Policy declaration for a tool."""
    tool_name: str
    risk_level: RiskLevel
    requires_approval: bool = False
    approval_threshold: Optional[float] = None  # e.g. amount in USD
    allowed_paths: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    max_affected_records: Optional[int] = None
    human_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "risk_level": self.risk_level.value,
            "requires_approval": self.requires_approval,
            "approval_threshold": self.approval_threshold,
            "allowed_paths": self.allowed_paths,
            "forbidden_patterns": self.forbidden_patterns,
            "max_affected_records": self.max_affected_records,
            "human_description": self.human_description,
        }


# Default policies for core tools (least-privilege by default)
DEFAULT_POLICIES: Dict[str, ToolPolicy] = {
    "bash": ToolPolicy(
        tool_name="bash",
        risk_level=RiskLevel.CRITICAL,
        requires_approval=True,
        forbidden_patterns=[
            "rm -rf /", "mkfs.", "dd if=", "> /dev/sd", "shutdown",
            "reboot", "format c:", ":(){:|:&};:", "chmod -R 777 /",
            "curl", "wget", "ssh", "scp", "sudo", "su -",
        ],
        human_description="Menjalankan perintah shell. Bisa merusak sistem.",
    ),
    "file_read": ToolPolicy(
        tool_name="file_read",
        risk_level=RiskLevel.READ_ONLY,
        requires_approval=False,
    ),
    "file_write": ToolPolicy(
        tool_name="file_write",
        risk_level=RiskLevel.MEDIUM,
        requires_approval=False,
        forbidden_patterns=["/etc/", "/usr/", "/boot/", "~/.ssh/", "~/.hermes/auth"],
    ),
    "file_search": ToolPolicy(
        tool_name="file_search",
        risk_level=RiskLevel.READ_ONLY,
        requires_approval=False,
    ),
    "web_search": ToolPolicy(
        tool_name="web_search",
        risk_level=RiskLevel.READ_ONLY,
        requires_approval=False,
    ),
    "calculate": ToolPolicy(
        tool_name="calculate",
        risk_level=RiskLevel.READ_ONLY,
        requires_approval=False,
    ),
}


# ============================================
# LAPIS 2 & 3: RUNTIME VALIDATION (di dalam tool)
# ============================================

class GuardrailViolation(Exception):
    """Raised when a tool action violates a guardrail."""

    def __init__(self, tool_name: str, reason: str, args: Dict[str, Any] = None):
        self.tool_name = tool_name
        self.reason = reason
        self.args = args or {}
        super().__init__(f"Guardrail violation in '{tool_name}': {reason}")


class ApprovalRequired(Exception):
    """Raised when a tool action requires human approval before execution."""

    def __init__(self, approval_request):
        self.approval_request = approval_request
        super().__init__(f"Approval required for '{approval_request.tool_name}'")


# ============================================
# LAPIS 4: APPROVAL GATE (Human-in-the-Loop)
# ============================================

@dataclass
class ApprovalRequest:
    """Rich approval payload — the human needs full context, not just yes/no."""
    id: str
    tool_name: str
    args: Dict[str, Any]
    risk_level: str
    irreversible: bool
    affected_scope: str  # e.g. "3,847 contacts" or "1 file"
    estimated_cost: str  # human-readable
    explanation: str
    status: str = "pending"  # pending | approved | rejected | edited
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    decided_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "args": self.args,
            "risk_level": self.risk_level,
            "irreversible": self.irreversible,
            "affected_scope": self.affected_scope,
            "estimated_cost": self.estimated_cost,
            "explanation": self.explanation,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "decided_by": self.decided_by,
        }


class ApprovalStore:
    """Persistent store for approval requests (PG-backed when available)."""

    def __init__(self):
        from aeryn_core.runtime.state_sharing import shared_connect
        self._shared_connect = shared_connect
        self.db_path = os.path.join(DATABASE_DIR, "approvals.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return self._shared_connect("approvals")

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    args TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    irreversible INTEGER DEFAULT 0,
                    affected_scope TEXT DEFAULT '',
                    estimated_cost TEXT DEFAULT '',
                    explanation TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    created_at REAL,
                    resolved_at REAL,
                    decided_by TEXT DEFAULT ''
                )
            """)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    def create(self, req: ApprovalRequest) -> ApprovalRequest:
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT INTO approvals (id, tool_name, args, risk_level, irreversible, affected_scope, estimated_cost, explanation, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (req.id, req.tool_name, json.dumps(req.args), req.risk_level,
                 int(req.irreversible), req.affected_scope, req.estimated_cost,
                 req.explanation, req.status, req.created_at)
            )
            conn.commit()
            conn.close()
        return req

    def get(self, approval_id: str) -> Optional[ApprovalRequest]:
        conn = self._connect()
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        conn.close()
        if not row:
            return None
        # Map columns
        cols = ["id", "tool_name", "args", "risk_level", "irreversible",
                "affected_scope", "estimated_cost", "explanation", "status",
                "created_at", "resolved_at", "decided_by"]
        data = dict(zip(cols, row))
        req = ApprovalRequest(
            id=data["id"],
            tool_name=data["tool_name"],
            args=json.loads(data["args"]),
            risk_level=data["risk_level"],
            irreversible=bool(data["irreversible"]),
            affected_scope=data["affected_scope"],
            estimated_cost=data["estimated_cost"],
            explanation=data["explanation"],
            status=data["status"],
            created_at=data["created_at"],
            resolved_at=data["resolved_at"],
            decided_by=data["decided_by"],
        )
        return req

    def update_status(self, approval_id: str, status: str, decided_by: str = "", edited_args: Optional[Dict] = None):
        with self._lock:
            conn = self._connect()
            if edited_args:
                args_json = json.dumps(edited_args)
                conn.execute("UPDATE approvals SET args = ?, status = ?, resolved_at = ?, decided_by = ? WHERE id = ?",
                             (args_json, status, time.time(), decided_by, approval_id))
            else:
                conn.execute("UPDATE approvals SET status = ?, resolved_at = ?, decided_by = ? WHERE id = ?",
                             (status, time.time(), decided_by, approval_id))
            conn.commit()
            conn.close()

    def pending(self) -> List[ApprovalRequest]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM approvals WHERE status = 'pending' ORDER BY created_at ASC").fetchall()
        conn.close()
        cols = ["id", "tool_name", "args", "risk_level", "irreversible",
                "affected_scope", "estimated_cost", "explanation", "status",
                "created_at", "resolved_at", "decided_by"]
        result = []
        for row in rows:
            data = dict(zip(cols, row))
            result.append(ApprovalRequest(
                id=data["id"],
                tool_name=data["tool_name"],
                args=json.loads(data["args"]),
                risk_level=data["risk_level"],
                irreversible=bool(data["irreversible"]),
                affected_scope=data["affected_scope"],
                estimated_cost=data["estimated_cost"],
                explanation=data["explanation"],
                status=data["status"],
                created_at=data["created_at"],
                resolved_at=data["resolved_at"],
                decided_by=data["decided_by"],
            ))
        return result


# ============================================
# GUARDRAIL ENGINE (mengorkestrasi 4 lapis)
# ============================================

class GuardrailEngine:
    """Enforce 4-layer guardrails on every tool invocation."""

    def __init__(self, policies: Dict[str, ToolPolicy] = None):
        self.policies = policies or DEFAULT_POLICIES
        self.approval_store = ApprovalStore()
        self._blocked_until = {}  # tool_name -> timestamp (rate-limit after reject)

    def get_policy(self, tool_name: str) -> Optional[ToolPolicy]:
        return self.policies.get(tool_name)

    def check_tool(self, tool_name: str, args: Dict[str, Any]) -> None:
        """
        LAPIS 2+3: Runtime validation. Called BEFORE the tool body executes.
        Raises GuardrailViolation or ApprovalRequired.
        """
        policy = self.get_policy(tool_name)
        if policy is None:
            # Unknown tool: least-privilege — block by default
            raise GuardrailViolation(tool_name, "No policy defined for tool (deny-by-default)", args)

        # Check forbidden patterns
        args_str = json.dumps(args).lower()
        for pattern in policy.forbidden_patterns:
            if pattern.lower() in args_str:
                raise GuardrailViolation(tool_name, f"Forbidden pattern matched: '{pattern}'", args)

        # Check allowed paths (for file tools)
        if policy.allowed_paths and "path" in args:
            path = args["path"]
            if not any(path.startswith(allowed) for allowed in policy.allowed_paths):
                raise GuardrailViolation(tool_name, f"Path '{path}' outside allowed scope", args)

        # Check approval requirement
        if policy.requires_approval:
            # Rate-limit: if recently rejected, block immediately
            if tool_name in self._blocked_until and time.time() < self._blocked_until[tool_name]:
                raise GuardrailViolation(tool_name, "Tool temporarily blocked after rejection (30s cooldown)", args)

            approval = self._build_approval_request(tool_name, args, policy)
            self.approval_store.create(approval)
            raise ApprovalRequired(approval)

    def _build_approval_request(self, tool_name: str, args: Dict[str, Any], policy: ToolPolicy) -> ApprovalRequest:
        """Build a rich approval payload for the human."""
        approval_id = hashlib.sha256(f"{tool_name}:{json.dumps(args)}:{time.time()}".encode()).hexdigest()[:16]

        # Determine scope & cost heuristics
        affected_scope = self._estimate_scope(tool_name, args)
        estimated_cost = self._estimate_cost(tool_name, args)
        irreversible = policy.risk_level in (RiskLevel.CRITICAL, RiskLevel.IRREVERSIBLE, RiskLevel.HIGH)

        explanation = policy.human_description or f"Tool '{tool_name}' membutuhkan persetujuan manusia."

        return ApprovalRequest(
            id=approval_id,
            tool_name=tool_name,
            args=args,
            risk_level=policy.risk_level.value,
            irreversible=irreversible,
            affected_scope=affected_scope,
            estimated_cost=estimated_cost,
            explanation=explanation,
        )

    def _estimate_scope(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "bash":
            cmd = args.get("command", "")
            return f"1 shell command: '{cmd[:80]}'"
        if tool_name == "file_write":
            return f"1 file: '{args.get('path', '?')}'"
        return "unknown scope"

    def _estimate_cost(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "bash":
            return "potensial merusak sistem (irreversible)"
        if tool_name == "file_write":
            return "menimpa 1 file"
        return "tidak ada biaya"

    def approve(self, approval_id: str, decided_by: str = "sen", edited_args: Optional[Dict] = None) -> Dict[str, Any]:
        """Approve a pending request. Optionally with edited args."""
        req = self.approval_store.get(approval_id)
        if not req:
            return {"error": "Approval not found"}
        if req.status != "pending":
            return {"error": f"Approval already {req.status}"}

        self.approval_store.update_status(approval_id, "approved", decided_by, edited_args)
        return {"status": "approved", "id": approval_id, "edited_args": edited_args}

    def reject(self, approval_id: str, decided_by: str = "sen") -> Dict[str, Any]:
        """Reject a pending request. Blocks the tool for 30s."""
        req = self.approval_store.get(approval_id)
        if not req:
            return {"error": "Approval not found"}

        self.approval_store.update_status(approval_id, "rejected", decided_by)
        # Cooldown block
        self._blocked_until[req.tool_name] = time.time() + 30
        return {"status": "rejected", "id": approval_id, "cooldown": "30s"}


# Global instance
_engine = None

def get_guardrail_engine() -> GuardrailEngine:
    global _engine
    if _engine is None:
        _engine = GuardrailEngine()
    return _engine