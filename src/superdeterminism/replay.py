"""Hash-verified L0 cassette, anchors, splice, tail stability."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from superdeterminism.classify import classify_span
from superdeterminism.models import ReplayStatus, TAPE_VERSION, Trace

_MUTATING = ("refund", "commit", "payment", "delete", "send", "email", "payout", "charge")


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _hash(blob: str) -> str:
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def tape_from_traces(traces: list[Trace]) -> dict[str, Any]:
    records: dict[str, dict[str, str]] = {}
    for trace in traces:
        for span in trace.spans:
            node_id, _, _ = classify_span(span)
            key = f"{node_id}|{_hash(_canonical(span.input))}"
            blob = _canonical(span.output)
            records[key] = {"output": blob, "sha256": _hash(blob)}
    return {"tape_version": TAPE_VERSION, "records": records}


def verify_tape(tape: dict[str, Any]) -> bool:
    if tape.get("tape_version") != TAPE_VERSION:
        return False
    records = tape.get("records") or {}
    if not isinstance(records, dict):
        return False
    for rec in records.values():
        if not isinstance(rec, dict):
            return False
        if _hash(str(rec.get("output", ""))) != rec.get("sha256"):
            return False
    return True


def _mutating(node_id: str) -> bool:
    low = node_id.lower()
    return any(tok in low for tok in _MUTATING)


def splice_node(
    traces: list[Trace],
    node_id: str,
    tape: dict[str, Any],
    majority_output: Any,
) -> ReplayStatus:
    if not verify_tape(tape):
        return ReplayStatus.DIVERGED
    records = tape["records"]
    children: dict[str, set[str]] = defaultdict(set)
    for trace in traces:
        by_span: dict[str, str] = {}
        for span in trace.spans:
            nid, _, _ = classify_span(span)
            if span.span_id:
                by_span[span.span_id] = nid
        for span in trace.spans:
            nid, _, _ = classify_span(span)
            if span.parent_span_id and span.parent_span_id in by_span:
                children[by_span[span.parent_span_id]].add(nid)
    hit = 0
    miss = 0
    for trace in traces:
        for span in trace.spans:
            nid, _, _ = classify_span(span)
            if nid != node_id:
                continue
            synthesized = _canonical(majority_output)
            key = f"{nid}|{_hash(_canonical(span.input))}"
            rec = records.get(key)
            if rec is None or rec.get("output") != synthesized:
                if rec is None:
                    miss += 1
                    if _mutating(nid):
                        return ReplayStatus.REFUSED_MUTATING
                    continue
                if rec.get("output") != synthesized and _canonical(span.output) != synthesized:
                    miss += 1
                    continue
            hit += 1
            for child in children.get(nid, ()):
                # ponytail: child lookup by node id only; per-input child keys if traces fan out
                child_keys = [k for k in records if k.startswith(child + "|")]
                if child_keys:
                    hit += 1
                elif children.get(nid):
                    miss += 1
    if miss:
        return ReplayStatus.DIVERGED
    if hit or not children.get(node_id):
        return ReplayStatus.TAIL_STABLE
    return ReplayStatus.PREFIX_VERIFIED
