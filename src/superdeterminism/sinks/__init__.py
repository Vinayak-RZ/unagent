"""Observability sinks: file export + live pull → list[Trace]."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from superdeterminism.ingest import IngestError, load_traces, load_traces_path
from superdeterminism.models import CaptureStatus, Span, Trace


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _span(
    *,
    name: str,
    attributes: dict[str, Any] | None = None,
    input: Any = None,
    output: Any = None,
    tokens: int = 0,
    latency_ms: float = 0.0,
    error: bool = False,
    trace_id: str = "",
    span_id: str = "",
    start_ns: int = 0,
    end_ns: int = 0,
) -> Span:
    attrs = dict(attributes or {})
    return Span(
        name=name or "span",
        attributes=attrs,
        input=input,
        output=output,
        tokens=tokens,
        latency_ms=latency_ms,
        error=error,
        trace_id=trace_id,
        span_id=span_id,
        start_ns=start_ns,
        end_ns=end_ns,
        input_capture=CaptureStatus.PRESENT.value if input is not None else CaptureStatus.ABSENT.value,
        output_capture=CaptureStatus.PRESENT.value if output is not None else CaptureStatus.ABSENT.value,
    )


def _group_traces(spans: list[Span]) -> list[Trace]:
    buckets: dict[str, list[Span]] = {}
    for span in spans:
        tid = span.trace_id or "trace"
        buckets.setdefault(tid, []).append(span)
    return [Trace(spans=items, trace_id=tid) for tid, items in buckets.items()]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestError(f"sink file unreadable: {path}: {exc}") from exc


def _http_json(url: str, *, headers: dict[str, str], timeout: float = 30.0) -> Any:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise IngestError(f"live sink request failed: {exc}") from exc


def load_langfuse_file(path: Path) -> list[Trace]:
    data = _read_json(path)
    if isinstance(data, dict) and ("resourceSpans" in data or "traces" in data):
        return load_traces(data)
    observations: Any
    if isinstance(data, dict):
        observations = data.get("observations") or data.get("data") or []
    elif isinstance(data, list):
        observations = data
    else:
        observations = []
    if not isinstance(observations, list):
        raise IngestError("langfuse export: expected observations list")
    spans: list[Span] = []
    for item in observations:
        if not isinstance(item, dict):
            continue
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        attrs = dict(meta)
        usage = item.get("usage") if isinstance(item.get("usage"), dict) else {}
        tokens = _as_int(item.get("totalTokens", usage.get("totalTokens")))
        name = str(item.get("name") or "observation")
        if "gen_ai.operation.name" not in attrs and (name.startswith("chat") or "generation" in name.lower()):
            attrs.setdefault("gen_ai.operation.name", "chat")
        spans.append(
            _span(
                name=name,
                attributes=attrs,
                input=item.get("input"),
                output=item.get("output"),
                tokens=tokens,
                latency_ms=_as_float(item.get("latency")),
                error=str(item.get("level", "")).upper() == "ERROR" or bool(item.get("statusMessage")),
                trace_id=str(item.get("traceId") or item.get("trace_id") or ""),
                span_id=str(item.get("id") or ""),
                start_ns=_as_int(item.get("startTime")),
                end_ns=_as_int(item.get("endTime")),
            )
        )
    if not spans:
        raise IngestError("langfuse export: no observations")
    return _group_traces(spans)


def load_langsmith_file(path: Path) -> list[Trace]:
    data = _read_json(path)
    if isinstance(data, dict) and ("resourceSpans" in data or "traces" in data):
        return load_traces(data)
    runs = data.get("runs") if isinstance(data, dict) else data
    if not isinstance(runs, list):
        raise IngestError("langsmith export: expected runs list")
    spans: list[Span] = []
    for item in runs:
        if not isinstance(item, dict):
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        meta = extra.get("metadata") if isinstance(extra.get("metadata"), dict) else {}
        attrs = dict(meta)
        run_type = str(item.get("run_type") or item.get("type") or "")
        if run_type in {"llm", "chat"}:
            attrs.setdefault("gen_ai.operation.name", "chat")
        elif run_type == "tool":
            attrs.setdefault("gen_ai.operation.name", "execute_tool")
            attrs.setdefault("gen_ai.tool.name", item.get("name"))
        spans.append(
            _span(
                name=str(item.get("name") or "run"),
                attributes=attrs,
                input=item.get("inputs"),
                output=item.get("outputs"),
                tokens=_as_int(item.get("total_tokens")),
                error=bool(item.get("error")),
                trace_id=str(item.get("trace_id") or item.get("session_id") or ""),
                span_id=str(item.get("id") or ""),
                start_ns=_as_int(item.get("start_time")),
                end_ns=_as_int(item.get("end_time")),
            )
        )
    if not spans:
        raise IngestError("langsmith export: no runs")
    return _group_traces(spans)


def load_mlflow_file(path: Path) -> list[Trace]:
    data = _read_json(path)
    if isinstance(data, dict) and ("resourceSpans" in data or "traces" in data):
        return load_traces(data)
    traces_raw = data.get("traces") if isinstance(data, dict) else data
    if not isinstance(traces_raw, list):
        raise IngestError("mlflow export: expected traces list")
    spans: list[Span] = []
    for tr in traces_raw:
        if not isinstance(tr, dict):
            continue
        tid = str(tr.get("request_id") or tr.get("trace_id") or "")
        for item in tr.get("spans") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            spans.append(
                _span(
                    name=str(item.get("name") or "span"),
                    attributes=dict(attrs),
                    input=item.get("inputs"),
                    output=item.get("outputs"),
                    error=str(item.get("status_code", "")).upper() == "ERROR",
                    trace_id=tid,
                    span_id=str(item.get("span_id") or item.get("id") or ""),
                    start_ns=_as_int(item.get("start_time_unix_nano")),
                    end_ns=_as_int(item.get("end_time_unix_nano")),
                )
            )
    if not spans:
        raise IngestError("mlflow export: no spans")
    return _group_traces(spans)


def load_langfuse_live(
    *,
    host: str | None = None,
    public_key: str | None = None,
    secret_key: str | None = None,
    limit: int = 100,
) -> list[Trace]:
    host = (host or os.environ.get("LANGFUSE_HOST") or "https://cloud.langfuse.com").rstrip("/")
    public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        raise IngestError("langfuse live requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
    token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    data = _http_json(
        f"{host}/api/public/observations?limit={int(limit)}",
        headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
    )
    tmp = Path("/tmp/unagent_langfuse_live.json")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    return load_langfuse_file(tmp)


def load_langsmith_live(
    *,
    api_url: str | None = None,
    api_key: str | None = None,
    project: str | None = None,
    limit: int = 100,
) -> list[Trace]:
    api_url = (api_url or os.environ.get("LANGSMITH_ENDPOINT") or "https://api.smith.langchain.com").rstrip("/")
    api_key = api_key or os.environ.get("LANGSMITH_API_KEY")
    project = project or os.environ.get("LANGSMITH_PROJECT")
    if not api_key:
        raise IngestError("langsmith live requires LANGSMITH_API_KEY")
    query = f"limit={int(limit)}"
    if project:
        query += f"&session={urllib.parse.quote(project)}"
    data = _http_json(
        f"{api_url}/runs/?{query}",
        headers={"x-api-key": api_key, "Accept": "application/json"},
    )
    runs = data if isinstance(data, list) else data.get("runs") or data.get("data") or []
    tmp = Path("/tmp/unagent_langsmith_live.json")
    tmp.write_text(json.dumps({"runs": runs}), encoding="utf-8")
    return load_langsmith_file(tmp)


def load_mlflow_live(*, tracking_uri: str | None = None, experiment_id: str | None = None) -> list[Trace]:
    tracking_uri = (tracking_uri or os.environ.get("MLFLOW_TRACKING_URI") or "").rstrip("/")
    experiment_id = experiment_id or os.environ.get("MLFLOW_EXPERIMENT_ID")
    if not tracking_uri:
        raise IngestError("mlflow live requires MLFLOW_TRACKING_URI")
    if not experiment_id:
        raise IngestError("mlflow live requires MLFLOW_EXPERIMENT_ID")
    data = _http_json(
        f"{tracking_uri}/ajax-api/2.0/mlflow/traces?experiment_id={experiment_id}",
        headers={"Accept": "application/json"},
    )
    tmp = Path("/tmp/unagent_mlflow_live.json")
    tmp.write_text(json.dumps(data if isinstance(data, dict) else {"traces": data}), encoding="utf-8")
    return load_mlflow_file(tmp)


_FILE = {
    "langfuse": load_langfuse_file,
    "langsmith": load_langsmith_file,
    "mlflow": load_mlflow_file,
}
_LIVE = {
    "langfuse": load_langfuse_live,
    "langsmith": load_langsmith_live,
    "mlflow": load_mlflow_live,
}


def load_sink(name: str, *, path: Path | None = None, live: bool = False) -> list[Trace]:
    key = name.lower().strip()
    if key not in _FILE:
        raise IngestError(f"unknown sink: {name}")
    if live:
        return _LIVE[key]()
    if path is None:
        raise IngestError("sink file path required unless --live")
    return _FILE[key](path)


def load_sink_or_path(
    *,
    sink: str | None,
    path: Path | None,
    live: bool = False,
    outcome_attr: str | None = None,
) -> list[Trace]:
    if sink:
        return load_sink(sink, path=path, live=live)
    if path is None:
        raise IngestError("traces path or --sink required")
    return load_traces_path(path, outcome_attr=outcome_attr)
