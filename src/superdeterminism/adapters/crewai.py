"""CrewAI / role-task loop adapter. Maps kickoff traces → Trace.

No hard dependency on the crewai package — maps exported JSON only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from superdeterminism.ingest import IngestError, load_traces, load_traces_path
from superdeterminism.models import Span, Trace

_CREW_MARKERS = frozenset({"crewai", "crew", "kickoff", "TaskOutput", "AgentAction"})


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    payload = _payload(path_or_bytes)
    if _looks_langgraph_only(payload):
        raise IngestError(
            "refuse: payload looks like LangGraph/LangSmith — use --adapter langgraph, not crewai"
        )
    if (isinstance(payload, dict) and "crew" in payload) or _has_crew_events(payload):
        return [_from_crew_export(payload)]
    # Fall through to generic ingest after light attribute normalization
    traces = _ingest(path_or_bytes, payload)
    return [Trace(spans=[_normalize(s) for s in t.spans], trace_id=t.trace_id) for t in traces]


def _payload(path_or_bytes: Path | str | bytes) -> Any:
    if isinstance(path_or_bytes, bytes):
        return json.loads(path_or_bytes.decode("utf-8"))
    return json.loads(Path(path_or_bytes).read_text(encoding="utf-8"))


def _ingest(path_or_bytes: Path | str | bytes, payload: Any) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        return load_traces(payload)
    return load_traces_path(Path(path_or_bytes))


def _has_crew_events(payload: Any) -> bool:
    if isinstance(payload, dict):
        if payload.get("framework") in {"crewai", "crew"}:
            return True
        events = payload.get("events") or payload.get("tasks") or []
        blob = json.dumps(events)[:4000].lower()
        return any(m.lower() in blob for m in _CREW_MARKERS)
    return False


def _looks_langgraph_only(payload: Any) -> bool:
    blob = json.dumps(payload)[:8000]
    has_lg = "langgraph_node" in blob or "langgraph_checkpoint" in blob
    has_crew = any(m in blob for m in ("crewai", "kickoff", "TaskOutput"))
    return has_lg and not has_crew


def _from_crew_export(payload: Any) -> Trace:
    spans: list[Span] = []
    if not isinstance(payload, dict):
        raise IngestError("crewai export must be a JSON object")
    events = payload.get("events") or []
    tasks = payload.get("tasks") or []
    for i, ev in enumerate(events if isinstance(events, list) else []):
        if not isinstance(ev, dict):
            continue
        spans.append(_event_span(ev, i))
    if not spans and isinstance(tasks, list):
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue
            agent = str(task.get("agent") or task.get("agent_role") or "agent")
            spans.append(
                Span(
                    name=f"agent {agent}",
                    attributes={
                        "gen_ai.operation.name": "chat",
                        "gen_ai.agent.name": agent,
                        "crewai.task": task.get("description") or task.get("name") or f"task_{i}",
                    },
                    input=task.get("input") or task.get("description"),
                    output=task.get("output") or task.get("result"),
                    error=bool(task.get("error")),
                    span_id=f"crew-task-{i}",
                    trace_id=str(payload.get("run_id") or "crew"),
                )
            )
            for j, tool in enumerate(task.get("tools") or []):
                if not isinstance(tool, dict):
                    continue
                spans.append(
                    Span(
                        name=f"execute_tool {tool.get('name') or j}",
                        attributes={
                            "gen_ai.operation.name": "execute_tool",
                            "gen_ai.tool.name": tool.get("name") or f"tool_{j}",
                        },
                        input=tool.get("input"),
                        output=tool.get("output"),
                        error=bool(tool.get("error")),
                        span_id=f"crew-tool-{i}-{j}",
                        trace_id=str(payload.get("run_id") or "crew"),
                        parent_span_id=f"crew-task-{i}",
                    )
                )
    if not spans:
        raise IngestError("crewai export: no events/tasks to map")
    return Trace(spans=spans, trace_id=str(payload.get("run_id") or "crew"))


def _event_span(ev: dict[str, Any], i: int) -> Span:
    kind = str(ev.get("type") or ev.get("event") or "").lower()
    agent = str(ev.get("agent") or ev.get("role") or "agent")
    if "tool" in kind:
        attrs = {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": ev.get("tool") or ev.get("name") or "tool",
        }
        name = f"execute_tool {attrs['gen_ai.tool.name']}"
    else:
        attrs = {
            "gen_ai.operation.name": "chat",
            "gen_ai.agent.name": agent,
        }
        name = f"agent {agent}"
    return Span(
        name=name,
        attributes=attrs,
        input=ev.get("input"),
        output=ev.get("output"),
        error=bool(ev.get("error")),
        span_id=str(ev.get("id") or f"crew-ev-{i}"),
        trace_id=str(ev.get("run_id") or "crew"),
    )


def _normalize(span: Span) -> Span:
    attrs = dict(span.attributes)
    if "crewai" in json.dumps(attrs).lower() and "gen_ai.operation.name" not in attrs:
        attrs["gen_ai.operation.name"] = "chat"
    if attrs == span.attributes:
        return span
    return Span(
        name=span.name,
        attributes=attrs,
        input=span.input,
        output=span.output,
        tokens=span.tokens,
        latency_ms=span.latency_ms,
        error=span.error,
        trace_id=span.trace_id,
        span_id=span.span_id,
        parent_span_id=span.parent_span_id,
        start_ns=span.start_ns,
        end_ns=span.end_ns,
        producer=span.producer,
        input_capture=span.input_capture,
        output_capture=span.output_capture,
    )
