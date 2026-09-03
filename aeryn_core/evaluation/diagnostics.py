"""Diagnostic Tools — failure attribution & trace-back.

Berdasarkan riset (Samira Ghodratnama): "trace back which agent's suggestion
introduced the error. A structured failure log (identifying culprit agent and
step) is very useful for debugging agent teams."

Purpose: when an evaluation episode fails, pinpoint WHICH step/agent/tool
introduced the error, not just "it failed".
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR
from aeryn_core.observability.tracing import get_trace_collector


@dataclass
class FailureAttribution:
    """Pinpoints the culprit of a failed episode."""
    episode_id: str
    culprit_step: str  # which agent/step/tool
    reason: str
    trace_id: str = ""
    severity: str = "unknown"  # low | medium | high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "culprit_step": self.culprit_step,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "severity": self.severity,
        }


class DiagnosticEngine:
    """Analyze failed episodes and attribute failure to specific steps."""

    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "diagnostics.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS failure_attributions (
                episode_id TEXT PRIMARY KEY,
                culprit_step TEXT,
                reason TEXT,
                trace_id TEXT,
                severity TEXT
            )
        """)
        conn.commit()
        conn.close()

    def attribute_failure(self, episode_id: str, trace_id: str = "") -> FailureAttribution:
        """Analyze a trace to find the culprit step."""
        culprit = "unknown"
        reason = "no trace available"
        severity = "unknown"

        if trace_id:
            collector = get_trace_collector()
            spans = collector.get_trace(trace_id)

            # Find error spans
            error_spans = [s for s in spans if s.status == "error"]
            if error_spans:
                # The first error span is usually the culprit
                culprit_span = error_spans[0]
                culprit = culprit_span.name
                reason = f"span '{culprit_span.name}' failed"
                severity = "high"

                # If it's a tool span, specify which tool
                tool_name = culprit_span.attributes.get("gen_ai.tool.name")
                if tool_name:
                    culprit = f"tool:{tool_name}"
                    reason = f"tool '{tool_name}' execution failed"

            # Check for token blow-up (loop detection)
            total_tokens = collector.get_token_total(trace_id)
            if total_tokens > 10000:  # 10k tokens = likely loop
                culprit = "agent_loop"
                reason = f"token blow-up detected ({total_tokens} tokens, likely stuck in loop)"
                severity = "high"

        attribution = FailureAttribution(
            episode_id=episode_id,
            culprit_step=culprit,
            reason=reason,
            trace_id=trace_id,
            severity=severity,
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO failure_attributions (episode_id, culprit_step, reason, trace_id, severity) VALUES (?,?,?,?,?)",
            (episode_id, culprit, reason, trace_id, severity)
        )
        conn.commit()
        conn.close()

        return attribution

    def get_attribution(self, episode_id: str) -> Optional[FailureAttribution]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT * FROM failure_attributions WHERE episode_id = ?", (episode_id,)).fetchone()
        conn.close()
        if not row:
            return None
        cols = ["episode_id", "culprit_step", "reason", "trace_id", "severity"]
        data = dict(zip(cols, row))
        return FailureAttribution(
            episode_id=data["episode_id"],
            culprit_step=data["culprit_step"],
            reason=data["reason"],
            trace_id=data["trace_id"],
            severity=data["severity"],
        )

    def list_attributions(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM failure_attributions LIMIT ?", (limit,)).fetchall()
        conn.close()
        cols = ["episode_id", "culprit_step", "reason", "trace_id", "severity"]
        return [dict(zip(cols, row)) for row in rows]


# Global instance
_engine = None

def get_diagnostic_engine() -> DiagnosticEngine:
    global _engine
    if _engine is None:
        _engine = DiagnosticEngine()
    return _engine