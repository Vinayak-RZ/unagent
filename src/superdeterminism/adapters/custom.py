"""Minimal custom-stack adapter: house JSON {traces:[{spans:[...]}]} or events[]."""

from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.ingest import load_traces, load_traces_path
from superdeterminism.models import Span, Trace


def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    if isinstance(path_or_bytes, bytes):
        payload = json.loads(path_or_bytes.decode("utf-8"))
    else:
        payload = json.loads(Path(path_or_bytes).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "events" in payload:
        spans = []
        for i, ev in enumerate(payload["events"]):
            if not isinstance(ev, dict):
                continue
            spans.append(
                Span(
                    name=str(ev.get("name") or "event"),
                    attributes={
                        "gen_ai.operation.name": ev.get("op") or "chat",
                        "langgraph_node": ev.get("node") or ev.get("name") or "event",
                    },
                    input=ev.get("input"),
                    output=ev.get("output"),
                    error=bool(ev.get("error")),
                    span_id=f"e{i}",
                    trace_id="custom",
                )
            )
        return [Trace(spans=spans, trace_id="custom")]
    if isinstance(path_or_bytes, bytes):
        return load_traces(payload)
    return load_traces_path(Path(path_or_bytes))
