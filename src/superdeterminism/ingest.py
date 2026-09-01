"""Boundary validation and OTLP/flat ingest. Untrusted input."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from superdeterminism.models import CaptureStatus, SCHEMA_VERSION, Span, Trace

MAX_BYTES = 32 * 1024 * 1024
MAX_SPANS = 100_000
MAX_DEPTH = 32


class IngestError(ValueError):
    """Malformed or oversized trace payload."""


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, dict):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, dict):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _attr_get(attrs: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in attrs and attrs[key] not in (None, ""):
            return attrs[key]
    return None


def _unwrap_otlp_value(value: Any, depth: int = 0) -> Any:
    if depth > MAX_DEPTH:
        raise IngestError("attribute nesting exceeds limit")
    if not isinstance(value, dict):
        return value
    for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if k in value:
            raw = value[k]
            if k == "intValue" and isinstance(raw, str):
                return _as_int(raw)
            return raw
    if "arrayValue" in value:
        return [
            _unwrap_otlp_value(v, depth + 1)
            for v in (value["arrayValue"] or {}).get("values", [])
        ]
    return value


def _otlp_attrs(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    out: dict[str, Any] = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict) or "key" not in item:
            continue
        out[str(item["key"])] = _unwrap_otlp_value(item.get("value"))
    return out


def _is_error(item: dict[str, Any], attrs: dict[str, Any]) -> bool:
    status = item.get("status")
    if isinstance(status, dict):
        code = status.get("code")
        if code in (2, "2", "STATUS_CODE_ERROR", "ERROR"):
            return True
        if code in (0, 1, "0", "1", "STATUS_CODE_UNSET", "STATUS_CODE_OK", "OK", "UNSET"):
            pass
        elif isinstance(status.get("code"), str) and "ERROR" in str(status["code"]).upper():
            return True
    elif status == "ERROR":
        return True
    err = item.get("error")
    if err is True or err == 1:
        return True
    if err in (False, 0, "false", "False", "0"):
        return False
    reasons = attrs.get("gen_ai.response.finish_reasons")
    if reasons is None:
        reasons = attrs.get("gen_ai.response.finish_reason")
    if isinstance(reasons, str):
        reasons = [reasons]
    if isinstance(reasons, list) and any(str(r).lower() == "error" for r in reasons):
        return True
    return False


def _capture(value: Any) -> str:
    if value is None:
        return CaptureStatus.ABSENT.value
    return CaptureStatus.PRESENT.value


def _producer(attrs: dict[str, Any]) -> str:
    return str(
        _attr_get(
            attrs,
            "telemetry.sdk.name",
            "gen_ai.provider.name",
            "gen_ai.system",
            "langsmith.span.kind",
        )
        or "unknown"
    )


def _tokens(item: dict[str, Any], attrs: dict[str, Any]) -> int:
    raw = item.get("tokens")
    if raw is None:
        raw = _attr_get(
            attrs,
            "gen_ai.usage.input_tokens",
            "gen_ai.usage.prompt_tokens",
        )
    return _as_int(raw, 0)


def _latency_ms(item: dict[str, Any]) -> float:
    if item.get("latency_ms") not in (None, ""):
        return _as_float(item.get("latency_ms"))
    start = _as_int(item.get("startTimeUnixNano") or item.get("start_time_unix_nano"))
    end = _as_int(item.get("endTimeUnixNano") or item.get("end_time_unix_nano"))
    if start and end and end >= start:
        return (end - start) / 1_000_000.0
    return 0.0


def _bool01(value: Any) -> float | None:
    if value is None:
        return None
    if value in (True, 1, "1", "true", "True"):
        return 1.0
    if value in (False, 0, "0", "false", "False"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def span_from_mapping(
    item: Any,
    *,
    default_trace_id: str = "",
    seq: int = 0,
    outcome_attr: str | None = None,
) -> Span:
    if not isinstance(item, dict):
        raise IngestError("span must be an object")
    attrs = item.get("attributes", {})
    if isinstance(attrs, list):
        attrs = _otlp_attrs(attrs)
    elif not isinstance(attrs, dict):
        attrs = {}
    attrs = dict(attrs)
    attrs.setdefault("advisor.schema_version", SCHEMA_VERSION)
    input_val = item.get("input")
    output_val = item.get("output")
    if output_val is None:
        output_val = _attr_get(attrs, "gen_ai.output.messages", "gen_ai.completion")
    trace_id = str(
        item.get("traceId") or item.get("trace_id") or default_trace_id or ""
    )
    span_id = str(item.get("spanId") or item.get("span_id") or f"s{seq}")
    parent = str(item.get("parentSpanId") or item.get("parent_span_id") or "")
    return Span(
        name=str(item.get("name") or item.get("span_name") or "unnamed"),
        attributes=attrs,
        input=input_val,
        output=output_val,
        tokens=_tokens(item, attrs),
        latency_ms=_latency_ms(item),
        error=_is_error(item, attrs),
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent,
        start_ns=_as_int(item.get("startTimeUnixNano") or item.get("start_time_unix_nano")),
        end_ns=_as_int(item.get("endTimeUnixNano") or item.get("end_time_unix_nano")),
        producer=_producer(attrs),
        input_capture=_capture(input_val),
        output_capture=_capture(output_val),
    )


def _trace_outcome(spans: list[Span], outcome_attr: str | None) -> tuple[float | None, float | None]:
    success = None
    policy = None
    for span in spans:
        attrs = span.attributes
        if success is None:
            success = _bool01(attrs.get("advisor.outcome.success"))
        if policy is None:
            policy = _bool01(attrs.get("advisor.outcome.policy_ok"))
        if outcome_attr and success is None:
            success = _bool01(attrs.get(outcome_attr))
    return success, policy


def _iter_otlp_spans(payload: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(payload, dict):
        return
    resources = payload.get("resourceSpans") or payload.get("resource_spans") or []
    if not isinstance(resources, list):
        raise IngestError("resourceSpans must be a list")
    for resource in resources:
        if not isinstance(resource, dict):
            raise IngestError("resource span must be an object")
        scopes = resource.get("scopeSpans") or resource.get("scope_spans") or []
        for scope in scopes:
            if not isinstance(scope, dict):
                raise IngestError("scope span must be an object")
            for span in scope.get("spans") or []:
                if not isinstance(span, dict):
                    raise IngestError("OTLP span must be an object")
                yield span


def _check_span_budget(n: int) -> None:
    if n > MAX_SPANS:
        raise IngestError(f"span count {n} exceeds limit {MAX_SPANS}")


def load_traces(payload: Any, *, outcome_attr: str | None = None) -> list[Trace]:
    """Accept OTLP JSON, {traces: [...]}, a list of traces, or a list of spans."""
    if isinstance(payload, dict) and (
        "resourceSpans" in payload or "resource_spans" in payload
    ):
        raw_spans = list(_iter_otlp_spans(payload))
        _check_span_budget(len(raw_spans))
        spans = [
            span_from_mapping(s, default_trace_id="otlp", seq=i, outcome_attr=outcome_attr)
            for i, s in enumerate(raw_spans)
        ]
        success, policy = _trace_outcome(spans, outcome_attr)
        tid = spans[0].trace_id if spans else "otlp"
        return [Trace(spans=spans, trace_id=tid, outcome_success=success, policy_ok=policy)]
    if isinstance(payload, dict) and "traces" in payload:
        raw = payload["traces"]
        if not isinstance(raw, list):
            raise IngestError("traces must be a list")
        traces: list[Trace] = []
        total = 0
        for i, t in enumerate(raw):
            if not isinstance(t, dict):
                raise IngestError("each trace must be an object")
            spans_raw = t.get("spans", [])
            if not isinstance(spans_raw, list):
                raise IngestError("spans must be a list")
            total += len(spans_raw)
            _check_span_budget(total)
            tid = str(t.get("trace_id") or t.get("id") or f"t{i}")
            spans = [
                span_from_mapping(s, default_trace_id=tid, seq=j, outcome_attr=outcome_attr)
                for j, s in enumerate(spans_raw)
            ]
            success, policy = _trace_outcome(spans, outcome_attr)
            traces.append(
                Trace(spans=spans, trace_id=tid, outcome_success=success, policy_ok=policy)
            )
        return traces
    if isinstance(payload, list) and payload:
        if not all(isinstance(x, dict) for x in payload):
            raise IngestError("list payload must contain objects")
        if "spans" in payload[0]:
            traces = []
            total = 0
            for i, t in enumerate(payload):
                spans_raw = t.get("spans", [])
                if not isinstance(spans_raw, list):
                    raise IngestError("spans must be a list")
                total += len(spans_raw)
                _check_span_budget(total)
                tid = str(t.get("trace_id") or f"t{i}")
                spans = [
                    span_from_mapping(s, default_trace_id=tid, seq=j)
                    for j, s in enumerate(spans_raw)
                ]
                success, policy = _trace_outcome(spans, outcome_attr)
                traces.append(
                    Trace(spans=spans, trace_id=tid, outcome_success=success, policy_ok=policy)
                )
            return traces
        _check_span_budget(len(payload))
        spans = [span_from_mapping(s, default_trace_id="flat", seq=i) for i, s in enumerate(payload)]
        success, policy = _trace_outcome(spans, outcome_attr)
        return [Trace(spans=spans, trace_id="flat", outcome_success=success, policy_ok=policy)]
    raise IngestError("unrecognized trace payload")


def load_traces_path(
    path: Path,
    *,
    outcome_attr: str | None = None,
    max_bytes: int = MAX_BYTES,
) -> list[Trace]:
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise IngestError(f"file exceeds {max_bytes} bytes")
    try:
        payload = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestError(str(exc)) from exc
    return load_traces(payload, outcome_attr=outcome_attr)


def load_traces_dir(directory: Path, *, outcome_attr: str | None = None) -> list[Trace]:
    traces: list[Trace] = []
    for path in sorted(directory.glob("*.json")):
        traces.extend(load_traces_path(path, outcome_attr=outcome_attr))
        _check_span_budget(sum(len(t.spans) for t in traces))
    if not traces:
        raise IngestError("no json traces in directory")
    return traces
