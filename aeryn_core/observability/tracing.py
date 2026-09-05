"""Observability — OTel GenAI Semantic Conventions tracing.

Per research (OpenTelemetry GenAI SIG, Zylos Research):
- Span types: `chat` (LLM call), `invoke_agent` (agent), `execute_tool` (tool)
- Attributes under `gen_ai.*` namespace: token usage, model, latency, finish reason
- Token cost = both cost center AND functional signal (detect loops)
- Session-level metrics for SLOs

This is a lightweight OTel-compliant implementation. Spans use the
OpenTelemetry GenAI semantic convention naming and attribute keys so they
can be exported to any OTel backend (Datadog, Honeycomb, New Relic, MLflow).
No heavy dependency — pure Python trace tree persisted to SQLite.
"""

import os
import json
import time
import uuid
import sqlite3
import threading
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


# GenAI semantic convention span names / attributes (OTel GenAI SIG)
SPAN_CHAT = "chat"
SPAN_AGENT = "invoke_agent"
SPAN_TOOL = "execute_tool"

# gen_ai.* attribute keys (OTel GenAI semantic conventions)
ATTR_OPERATION = "gen_ai.operation.name"
ATTR_SYSTEM = "gen_ai.system"
ATTR_MODEL = "gen_ai.request.model"
ATTR_TOKENS_INPUT = "gen_ai.usage.input_tokens"
ATTR_TOKENS_OUTPUT = "gen_ai.usage.output_tokens"
ATTR_TOKENS_TOTAL = "gen_ai.usage.total_tokens"
ATTR_FINISH_REASON = "gen_ai.response.finish_reasons"
ATTR_AGENT_NAME = "gen_ai.agent.name"
ATTR_TOOL_NAME = "gen_ai.tool.name"
ATTR_SESSION = "gen_ai.session.id"


@dataclass
class Span:
    """An OTel-compliant GenAI span."""
    id: str
    trace_id: str
    parent_id: Optional[str]
    name: str  # chat | invoke_agent | execute_tool
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "unset"  # unset | ok | error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round((self.end_time - self.start_time) * 1000, 2) if self.end_time else None,
            "attributes": self.attributes,
            "status": self.status,
        }


class TraceCollector:
    """Collects spans into a trace tree, persisted (PG-backed when available)."""

    def __init__(self):
        from aeryn_core.runtime.state_sharing import shared_connect
        self._shared_connect = shared_connect
        self.db_path = os.path.join(DATABASE_DIR, "traces.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return self._shared_connect("traces")

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spans (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    parent_id TEXT,
                    name TEXT NOT NULL,
                    start_time REAL,
                    end_time REAL,
                    attributes TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'unset'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_name ON spans(name)")
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    def start_span(self, trace_id: str, parent_id: Optional[str], name: str, attributes: Dict[str, Any] = None) -> Span:
        span = Span(
            id=str(uuid.uuid4().hex[:16]),
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        return span

    def end_span(self, span: Span, status: str = "ok", attributes: Dict[str, Any] = None):
        span.end_time = time.time()
        span.status = status
        if attributes:
            span.attributes.update(attributes)

        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT INTO spans (id, trace_id, parent_id, name, start_time, end_time, attributes, status) VALUES (?,?,?,?,?,?,?,?)",
                (span.id, span.trace_id, span.parent_id, span.name,
                 span.start_time, span.end_time, json.dumps(span.attributes), span.status)
            )
            conn.commit()
            conn.close()

    def get_trace(self, trace_id: str) -> List[Span]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time ASC", (trace_id,)).fetchall()
        conn.close()

        cols = ["id", "trace_id", "parent_id", "name", "start_time", "end_time", "attributes", "status"]
        spans = []
        for row in rows:
            data = dict(zip(cols, row))
            spans.append(Span(
                id=data["id"],
                trace_id=data["trace_id"],
                parent_id=data["parent_id"],
                name=data["name"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                attributes=json.loads(data["attributes"]),
                status=data["status"],
            ))
        return spans

    def get_token_total(self, trace_id: str) -> int:
        """Sum total tokens across a trace (for cost + loop detection)."""
        spans = self.get_trace(trace_id)
        total = 0
        for s in spans:
            total += s.attributes.get(ATTR_TOKENS_TOTAL, 0) or 0
        return total

    def list_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT trace_id, MIN(start_time) as first, MAX(end_time) as last, COUNT(*) as span_count FROM spans GROUP BY trace_id ORDER BY first DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [
            {"trace_id": r[0], "start": r[1], "end": r[2], "span_count": r[3]}
            for r in rows
        ]


# Global collector
_collector = None

def get_trace_collector() -> TraceCollector:
    global _collector
    if _collector is None:
        _collector = TraceCollector()
    return _collector


class TraceContext:
    """Context manager for tracing a block of work as a span."""

    def __init__(self, collector: TraceCollector, trace_id: str, parent_id: Optional[str], name: str, attributes: Dict[str, Any] = None):
        self.collector = collector
        self.span = collector.start_span(trace_id, parent_id, name, attributes)

    def __enter__(self) -> Span:
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "ok"
        self.collector.end_span(self.span, status=status)


def start_trace(session_id: str = "") -> str:
    """Start a new trace, returns trace_id."""
    trace_id = str(uuid.uuid4().hex[:16])
    # Record trace metadata
    return trace_id


def trace(trace_id: str, parent_id: Optional[str], name: str, attributes: Dict[str, Any] = None) -> TraceContext:
    """Create a trace span context."""
    collector = get_trace_collector()
    return TraceContext(collector, trace_id, parent_id, name, attributes)