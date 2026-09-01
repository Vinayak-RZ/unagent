"""ATIF-shaped trajectory → core Trace. Complementary to OTLP; does not invent gen_ai.* beyond operation names we already consume."""

from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Span, Trace


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        payload = json.loads(path_or_bytes.decode("utf-8"))
    else:
        payload = json.loads(Path(path_or_bytes).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [_one(p, i) for i, p in enumerate(payload) if isinstance(p, dict)]
    if isinstance(payload, dict):
        return [_one(payload, 0)]
    raise ValueError("ATIF payload must be an object or list")


def _one(doc: dict, idx: int) -> Trace:
    tid = str(doc.get("trajectory_id") or doc.get("id") or f"atif{idx}")
    steps = doc.get("steps") or doc.get("trajectory") or []
    spans: list[Span] = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        kind = str(step.get("type") or step.get("role") or "").lower()
        if kind in {"tool_call", "tool", "function"}:
            op = "execute_tool"
            name = str(step.get("name") or step.get("tool") or "tool")
            attrs = {"gen_ai.operation.name": op, "gen_ai.tool.name": name}
            output = step.get("observation") or step.get("output")
            input_v = step.get("arguments") or step.get("input")
        else:
            op = "chat"
            name = str(step.get("name") or "assistant")
            attrs = {"gen_ai.operation.name": op, "gen_ai.agent.name": name}
            output = step.get("content") or step.get("output")
            input_v = step.get("input")
        spans.append(
            Span(
                name=name,
                attributes=attrs,
                input=input_v,
                output=output,
                error=bool(step.get("error")),
                trace_id=tid,
                span_id=f"{tid}-{i}",
            )
        )
    return Trace(spans=spans, trace_id=tid)
