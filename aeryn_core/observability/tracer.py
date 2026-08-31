#!/usr/bin/env python3
"""V61.1 — Observability & Tracing (Langfuse-style) for Aeryn.

Traces LLM calls, tool execution, and conversation spans.
Stores to JSONL for analysis. No external dependencies.
"""
import os
import sys
import json
import time
import uuid
import logging
import functools
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

TRACE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Personalisasi", "Traces")


class Span:
    """A single operation span (LLM call, tool execution, etc.)."""

    def __init__(self, name: str, span_type: str, input: Any = None, parent_id: str = None):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.span_type = span_type  # "llm", "tool", "retrieval", "generation"
        self.input = input
        self.output = None
        self.parent_id = parent_id
        self.trace_id = None
        self.start_time = time.time()
        self.end_time = None
        self.duration_ms = 0
        self.metadata: Dict[str, Any] = {}
        self.error = None

    def finish(self, output: Any = None, error: str = None):
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        self.output = output
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "type": self.span_type,
            "input": self._safe_serialize(self.input),
            "output": self._safe_serialize(self.output),
            "duration_ms": self.duration_ms,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "error": self.error,
        }

    def _safe_serialize(self, obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._safe_serialize(i) for i in obj]
        try:
            s = str(obj)
            return s[:1000] if len(s) > 1000 else s
        except:
            return "<unserializable>"


class Trace:
    """A conversation trace containing multiple spans."""

    def __init__(self, session_id: str, user_id: str = "default"):
        self.id = str(uuid.uuid4())[:12]
        self.session_id = session_id
        self.user_id = user_id
        self.spans: List[Span] = []
        self.start_time = time.time()
        self.end_time = None
        self.metadata: Dict[str, Any] = {}

    def add_span(self, span: Span):
        span.trace_id = self.id
        self.spans.append(span)
        return span

    def finish(self):
        self.end_time = time.time()

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "span_count": len(self.spans),
            "total_duration_ms": int((self.end_time - self.start_time) * 1000) if self.end_time else 0,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class Tracer:
    """Singleton tracer for collecting spans and traces."""

    def __init__(self):
        self._traces: Dict[str, Trace] = {}
        self._active_spans: Dict[str, Span] = {}
        self._enabled = True

    def start_trace(self, session_id: str, user_id: str = "default") -> Trace:
        trace = Trace(session_id, user_id)
        self._traces[trace.id] = trace
        return trace

    def start_span(self, name: str, span_type: str, input: Any = None, parent_id: str = None, trace_id: str = None) -> Span:
        span = Span(name, span_type, input, parent_id)
        span.trace_id = trace_id
        self._active_spans[span.id] = span
        if trace_id and trace_id in self._traces:
            self._traces[trace_id].add_span(span)
        return span

    def finish_span(self, span_id: str, output: Any = None, error: str = None):
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(output, error)

    def finish_trace(self, trace_id: str):
        trace = self._traces.get(trace_id)
        if trace:
            trace.finish()
            self._persist(trace)

    def _persist(self, trace: Trace):
        os.makedirs(TRACE_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d")
        path = os.path.join(TRACE_DIR, f"traces_{ts}.jsonl")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist trace: {e}")

    @contextmanager
    def trace_context(self, session_id: str, user_id: str = "default"):
        trace = self.start_trace(session_id, user_id)
        try:
            yield trace
        finally:
            self.finish_trace(trace.id)

    @contextmanager
    def span_context(self, name: str, span_type: str, input: Any = None, trace_id: str = None):
        span = self.start_span(name, span_type, input, trace_id=trace_id)
        try:
            yield span
            self.finish_span(span.id, output=getattr(span, '_output', None))
        except Exception as e:
            self.finish_span(span.id, error=str(e))
            raise

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        return self._traces.get(trace_id)

    def get_recent_traces(self, limit: int = 10) -> List[Dict]:
        traces = sorted(self._traces.values(), key=lambda t: t.start_time, reverse=True)[:limit]
        return [{"id": t.id, "session_id": t.session_id, "spans": len(t.spans)} for t in traces]

    def get_stats(self) -> Dict:
        total_traces = len(self._traces)
        total_spans = sum(len(t.spans) for t in self._traces.values())
        avg_spans = total_spans / total_traces if total_traces else 0
        return {
            "total_traces": total_traces,
            "total_spans": total_spans,
            "avg_spans_per_trace": round(avg_spans, 1),
            "active_spans": len(self._active_spans),
        }


# Singleton
_tracer = None

def get_tracer() -> Tracer:
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def trace_llm_call(func: Callable) -> Callable:
    """Decorator to automatically trace LLM calls."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracer = get_tracer()
        if not tracer._enabled:
            return func(*args, **kwargs)
        input_data = {"args": str(args)[:500], "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}}
        span = tracer.start_span(func.__name__, "llm", input_data)
        try:
            result = func(*args, **kwargs)
            span.finish(output=str(result)[:500] if result else None)
            return result
        except Exception as e:
            span.finish(error=str(e))
            raise
    return wrapper


def trace_tool_call(func: Callable) -> Callable:
    """Decorator to automatically trace tool execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracer = get_tracer()
        if not tracer._enabled:
            return func(*args, **kwargs)
        input_data = {"args": str(args)[:500], "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}}
        span = tracer.start_span(func.__name__, "tool", input_data)
        try:
            result = func(*args, **kwargs)
            output = result.to_dict() if hasattr(result, 'to_dict') else str(result)[:500]
            span.finish(output=output)
            return result
        except Exception as e:
            span.finish(error=str(e))
            raise
    return wrapper
