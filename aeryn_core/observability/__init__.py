"""Observability & Analytics — Tracing, Metrics, Langfuse Integration.

Diadaptasi dari:
- LangChain: Langfuse integration, trace/span tracking
- LobeHub: Analytics dashboard, usage metrics
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TraceStatus(Enum):
    """Status of a trace span."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Span:
    """A trace span."""
    id: str
    name: str
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: TraceStatus = TraceStatus.OK
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    def finish(self, status: TraceStatus = TraceStatus.OK, error: str = None):
        """Finish the span."""
        self.end_time = time.time()
        self.status = status
        if error:
            self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "metadata": self.metadata,
            "error": self.error,
        }


@dataclass
class Trace:
    """A trace containing multiple spans."""
    id: str
    name: str
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_span(self, span: Span):
        """Add a span to the trace."""
        self.spans.append(span)
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get a span by ID."""
        return next((s for s in self.spans if s.id == span_id), None)
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.spans:
            start = min(s.start_time for s in self.spans)
            end = max(s.end_time for s in self.spans if s.end_time)
            return (end - start) * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "duration_ms": self.duration_ms,
        }


class Tracer:
    """Custom tracer — diadaptasi dari LangChain tracers."""
    
    def __init__(self, service_name: str = "aeryn"):
        self.service_name = service_name
        self._traces: Dict[str, Trace] = {}
        self._active_spans: Dict[str, Span] = {}
    
    def start_trace(self, name: str, trace_id: str = None, metadata: Dict = None) -> Trace:
        """Start a new trace."""
        import uuid
        
        trace = Trace(
            id=trace_id or f"trace_{uuid.uuid4().hex[:16]}",
            name=name,
            metadata=metadata or {},
        )
        self._traces[trace.id] = trace
        return trace
    
    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_id: str = None,
        metadata: Dict = None,
    ) -> Span:
        """Start a new span."""
        import uuid
        
        span = Span(
            id=f"span_{uuid.uuid4().hex[:16]}",
            name=name,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        
        trace = self._traces.get(trace_id)
        if trace:
            trace.add_span(span)
        
        self._active_spans[span.id] = span
        return span
    
    def end_span(self, span_id: str, status: TraceStatus = TraceStatus.OK, error: str = None):
        """End a span."""
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(status, error)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)
    
    def list_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent traces."""
        traces = sorted(
            self._traces.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        return [t.to_dict() for t in traces[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        total_traces = len(self._traces)
        total_spans = sum(len(t.spans) for t in self._traces.values())
        error_traces = sum(
            1 for t in self._traces.values()
            if any(s.status == TraceStatus.ERROR for s in t.spans)
        )
        
        durations = [t.duration_ms for t in self._traces.values() if t.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_traces": total_traces,
            "total_spans": total_spans,
            "error_traces": error_traces,
            "error_rate": error_traces / total_traces if total_traces > 0 else 0,
            "avg_duration_ms": avg_duration,
        }


class LangfuseService:
    """Langfuse integration — diadaptasi dari LangChain."""
    
    def __init__(self, public_key: str = None, secret_key: str = None, host: str = None):
        self.public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
        self.host = host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self._client = None
        self._connect()
    
    def _connect(self):
        """Connect to Langfuse."""
        if not self.public_key or not self.secret_key:
            logger.warning("Langfuse credentials not configured")
            return
        
        try:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
            logger.info("Connected to Langfuse")
        except ImportError:
            logger.warning("Langfuse SDK not installed")
        except Exception as e:
            logger.error(f"Failed to connect to Langfuse: {e}")
    
    def trace(self, name: str, user_id: str = None, metadata: Dict = None):
        """Create a trace context."""
        if not self._client:
            return None
        
        return self._client.trace(
            name=name,
            user_id=user_id,
            metadata=metadata,
        )
    
    def span(self, name: str, trace=None, metadata: Dict = None):
        """Create a span."""
        if not self._client:
            return None
        
        if trace:
            return trace.span(name=name, metadata=metadata)
        return self._client.span(name=name, metadata=metadata)
    
    def flush(self):
        """Flush pending events."""
        if self._client:
            self._client.flush()
    
    def shutdown(self):
        """Shutdown Langfuse client."""
        if self._client:
            self._client.shutdown()


class MetricsCollector:
    """Collect and aggregate metrics — diadaptasi dari LobeHub."""
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._timestamps: Dict[str, datetime] = {}
    
    def increment(self, metric: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter."""
        key = self._build_key(metric, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        self._timestamps[key] = datetime.utcnow()
    
    def gauge(self, metric: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        key = self._build_key(metric, labels)
        self._gauges[key] = value
        self._timestamps[key] = datetime.utcnow()
    
    def histogram(self, metric: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value."""
        key = self._build_key(metric, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._timestamps[key] = datetime.utcnow()
    
    def _build_key(self, metric: str, labels: Dict[str, str] = None) -> str:
        """Build a metric key with labels."""
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{metric}{{{label_str}}}"
        return metric
    
    def get_counter(self, metric: str, labels: Dict[str, str] = None) -> int:
        """Get counter value."""
        key = self._build_key(metric, labels)
        return self._counters.get(key, 0)
    
    def get_gauge(self, metric: str, labels: Dict[str, str] = None) -> float:
        """Get gauge value."""
        key = self._build_key(metric, labels)
        return self._gauges.get(key, 0.0)
    
    def get_histogram(self, metric: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        key = self._build_key(metric, labels)
        values = self._histograms.get(key, [])
        
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            "count": n,
            "sum": sum(sorted_values),
            "avg": sum(sorted_values) / n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)],
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: self.get_histogram(k.split("{")[0])
                for k in self._histograms
            },
        }
    
    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timestamps.clear()


class AnalyticsService:
    """Analytics service — diadaptasi dari LobeHub."""
    
    def __init__(self, storage_path: str = "./analytics"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._events: List[Dict[str, Any]] = []
        self._metrics = MetricsCollector()
    
    def track_event(
        self,
        event_type: str,
        user_id: str = None,
        workspace_id: str = None,
        properties: Dict[str, Any] = None,
    ):
        """Track an event."""
        event = {
            "type": event_type,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "properties": properties or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._events.append(event)
        
        # Update metrics
        self._metrics.increment(f"events.{event_type}")
        if workspace_id:
            self._metrics.increment(f"events.workspace.{workspace_id}.{event_type}")
    
    def track_usage(
        self,
        user_id: str,
        workspace_id: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost: float = 0.0,
        endpoint: str = None,
    ):
        """Track usage for billing."""
        self.track_event(
            "usage",
            user_id=user_id,
            workspace_id=workspace_id,
            properties={
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "cost": cost,
                "endpoint": endpoint,
            },
        )
        
        # Update metrics
        self._metrics.increment("usage.total_requests")
        self._metrics.increment("usage.tokens_input", tokens_input)
        self._metrics.increment("usage.tokens_output", tokens_output)
        self._metrics.histogram("usage.cost", cost)
    
    def get_usage_summary(
        self,
        workspace_id: str = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get usage summary."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        events = [
            e for e in self._events
            if e["type"] == "usage"
            and datetime.fromisoformat(e["timestamp"]) > cutoff
            and (not workspace_id or e.get("workspace_id") == workspace_id)
        ]
        
        total_requests = len(events)
        total_tokens_input = sum(e["properties"].get("tokens_input", 0) for e in events)
        total_tokens_output = sum(e["properties"].get("tokens_output", 0) for e in events)
        total_cost = sum(e["properties"].get("cost", 0) for e in events)
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_cost": total_cost,
            "avg_tokens_per_request": (total_tokens_input + total_tokens_output) / total_requests if total_requests > 0 else 0,
        }
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get user activity."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        events = [
            e for e in self._events
            if e.get("user_id") == user_id
            and datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "events_by_type": self._group_by(events, "type"),
            "daily_activity": self._group_by_day(events),
        }
    
    def _group_by(self, events: List[Dict], key: str) -> Dict[str, int]:
        """Group events by a key."""
        result: Dict[str, int] = {}
        for e in events:
            value = e.get(key, "unknown")
            result[value] = result.get(value, 0) + 1
        return result
    
    def _group_by_day(self, events: List[Dict]) -> Dict[str, int]:
        """Group events by day."""
        result: Dict[str, int] = {}
        for e in events:
            day = e["timestamp"][:10]  # YYYY-MM-DD
            result[day] = result.get(day, 0) + 1
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return self._metrics.get_all_metrics()
    
    def export_events(self, path: str):
        """Export events to JSON."""
        with open(path, "w") as f:
            json.dump(self._events, f, indent=2)
    
    def import_events(self, path: str):
        """Import events from JSON."""
        with open(path) as f:
            self._events = json.load(f)
