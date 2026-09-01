"""Stratified evidence: trace as sampling unit, Wilson intervals, tiers."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from typing import Any

from superdeterminism.classify import classify_span
from superdeterminism.models import (
    DetClass,
    EvidenceTier,
    NodeKind,
    ReplayStatus,
    Trace,
)
from superdeterminism.replay import splice_node, tape_from_traces, verify_tape


def wilson_lower(successes: int, n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    phat = successes / n
    denom = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    spread = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return max(0.0, (centre - spread) / denom)


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _is_schema(value: Any) -> bool:
    if isinstance(value, (dict, list)):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text or text[0] not in "{[":
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, (dict, list))


def collect_node_stats(traces: list[Trace]) -> dict[str, dict[str, Any]]:
    """One observation per (trace, node_id). Mixed kinds are flagged, never last-write."""
    buckets: dict[str, dict[str, Any]] = {}
    for trace in traces:
        per_trace: dict[str, dict[str, Any]] = {}
        for span in trace.spans:
            node_id, kind, det = classify_span(span)
            row = per_trace.setdefault(
                node_id,
                {
                    "kinds": set(),
                    "dets": set(),
                    "outputs": [],
                    "errors": 0,
                    "tokens": 0.0,
                    "latency": 0.0,
                    "n_spans": 0,
                    "models": set(),
                },
            )
            row["kinds"].add(kind)
            row["dets"].add(det)
            row["outputs"].append(span.output)
            row["errors"] += int(span.error)
            row["tokens"] += span.tokens
            row["latency"] += span.latency_ms
            row["n_spans"] += 1
            model = str(span.attributes.get("gen_ai.request.model") or "")
            if model:
                row["models"].add(model)
        for node_id, row in per_trace.items():
            bucket = buckets.setdefault(
                node_id,
                {
                    "kinds": set(),
                    "dets": set(),
                    "outputs": [],
                    "errors": 0,
                    "n": 0,
                    "tokens": 0.0,
                    "latency": 0.0,
                    "task_success": [],
                    "policy_ok": [],
                    "models": set(),
                },
            )
            bucket["kinds"] |= row["kinds"]
            bucket["dets"] |= row["dets"]
            bucket["models"] |= row["models"]
            # ponytail: one output sample per trace (first); extra intra-trace calls stay in outputs for schema
            bucket["outputs"].extend(row["outputs"][:1])
            bucket["errors"] += int(row["errors"] > 0)
            bucket["n"] += 1
            bucket["tokens"] += row["tokens"]
            bucket["latency"] += row["latency"]
            if trace.outcome_success is not None:
                bucket["task_success"].append(trace.outcome_success)
            if trace.policy_ok is not None:
                bucket["policy_ok"].append(trace.policy_ok)
    out: dict[str, dict[str, Any]] = {}
    for node_id, bucket in buckets.items():
        n = int(bucket["n"])
        outputs = bucket["outputs"]
        canon = [_canonical(o) for o in outputs]
        counts = Counter(canon)
        mode_blob, mode_n = counts.most_common(1)[0] if counts else ("", 0)
        p_mode = mode_n / n if n else 0.0
        kinds = bucket["kinds"]
        mixed = len(kinds) > 1
        kind = next(iter(kinds)) if len(kinds) == 1 else NodeKind.UNKNOWN
        det = next(iter(bucket["dets"])) if len(bucket["dets"]) == 1 else DetClass.COMPOSITE
        ts = bucket["task_success"]
        po = bucket["policy_ok"]
        out[node_id] = {
            "kind": kind,
            "det": det,
            "mixed": mixed,
            "n": n,
            "p_mode": p_mode,
            "p_mode_lower": wilson_lower(mode_n, n),
            "schema_ok": sum(_is_schema(o) for o in outputs) / n if n else 0.0,
            "failure_rate": bucket["errors"] / n if n else 0.0,
            "cost_tokens": bucket["tokens"] / n if n else 0.0,
            "latency_ms": bucket["latency"] / n if n else 0.0,
            "majority": mode_blob,
            "majority_n": mode_n,
            "task_success": (sum(ts) / len(ts)) if ts else None,
            "policy_ok": (sum(po) / len(po)) if po else None,
            "unknown": kind is NodeKind.UNKNOWN or mixed,
            "mixed_workload": len(bucket["models"]) > 1,
        }
    return out


def attach_replay(
    traces: list[Trace],
    stats: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    tape = tape_from_traces(traces)
    tape_ok = verify_tape(tape)
    for node_id, row in stats.items():
        if not tape_ok:
            row["replay"] = ReplayStatus.DIVERGED
            row["tier"] = EvidenceTier.OBSERVATIONAL
            continue
        majority = row["majority"]
        try:
            majority_val = json.loads(majority) if majority.startswith(("{", "[")) else majority
        except json.JSONDecodeError:
            majority_val = majority
        status = splice_node(traces, node_id, tape, majority_val)
        if status is ReplayStatus.TAIL_STABLE and not row["unknown"] and not row["mixed"]:
            row["replay"] = status
            row["tier"] = EvidenceTier.CASSETTE
        else:
            row["tier"] = EvidenceTier.OBSERVATIONAL
            row["replay"] = (
                ReplayStatus.RESAMPLE_ONLY
                if status is ReplayStatus.TAIL_STABLE
                else status
            )
    return stats
