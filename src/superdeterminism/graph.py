"""Reconstruct architecture graph G=(V,E) from normalized traces."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from superdeterminism.models import (
    ArchitectureGraph,
    DetClass,
    EdgeKind,
    GraphEdge,
    GraphNode,
    NodeKind,
    SCHEMA_VERSION,
    Trace,
    TrustLevel,
)
from superdeterminism.classify import classify_span

_DROP = frozenset({"__start__", "__end__"})
_SIDE_EFFECT = ("refund", "commit", "payment", "delete", "send", "email", "write", "payout")


def _side_effect(node_id: str) -> bool:
    low = node_id.lower()
    return any(tok in low for tok in _SIDE_EFFECT)


def reconstruct(traces: list[Trace]) -> ArchitectureGraph:
    kinds: dict[str, set[NodeKind]] = defaultdict(set)
    dets: dict[str, DetClass] = {}
    missing_parent = 0
    unknown_n = 0
    warnings: list[str] = []
    edge_set: set[tuple[str, str, str]] = set()

    for trace in traces:
        by_id: dict[str, str] = {}
        for span in trace.spans:
            node_id, kind, det = classify_span(span)
            if node_id in _DROP:
                continue
            kinds[node_id].add(kind)
            dets[node_id] = det
            if kind is NodeKind.UNKNOWN:
                unknown_n += 1
            if span.span_id:
                by_id[span.span_id] = node_id
            triggers = span.attributes.get("langgraph_triggers")
            if triggers:
                targets = triggers if isinstance(triggers, list) else [triggers]
                for dst in targets:
                    dst_s = str(dst)
                    if dst_s and dst_s not in _DROP:
                        edge_set.add((node_id, dst_s, EdgeKind.CONTROL.value))
            tool = str(span.attributes.get("gen_ai.tool.name") or "")
            if tool.startswith("transfer_to_") or "handoff" in tool.lower() or "handoff" in span.name.lower():
                kinds[node_id].add(NodeKind.ROUTER)
                dets[node_id] = DetClass.DETERMINISTIC
                tgt = tool.replace("transfer_to_", "") if tool.startswith("transfer_to_") else ""
                if tgt:
                    edge_set.add((node_id, tgt, EdgeKind.HANDOFF.value))
        for span in trace.spans:
            node_id, _, _ = classify_span(span)
            if node_id in _DROP:
                continue
            parent = span.parent_span_id
            if parent:
                src = by_id.get(parent)
                if src and src != node_id:
                    edge_set.add((src, node_id, EdgeKind.PARENT.value))
                elif parent not in by_id:
                    missing_parent += 1

    nodes: list[GraphNode] = []
    for node_id in sorted(kinds):
        kset = kinds[node_id]
        mixed = len(kset) > 1
        kind = next(iter(kset)) if len(kset) == 1 else NodeKind.UNKNOWN
        if NodeKind.ROUTER in kset and not mixed:
            kind = NodeKind.ROUTER
        det = dets.get(node_id, DetClass.COMPOSITE)
        decision = kind in {
            NodeKind.LLM_REASONER,
            NodeKind.ROUTER,
            NodeKind.SUBAGENT,
            NodeKind.WORKFLOW,
        }
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=kind,
                det_class=det,
                mixed=mixed,
                side_effects=_side_effect(node_id),
                is_decision=decision and not _side_effect(node_id),
            )
        )
        if mixed:
            warnings.append(f"mixed kinds on {node_id}")

    edges = [
        GraphEdge(src=a, dst=b, kind=EdgeKind(k))
        for a, b, k in sorted(edge_set)
        if a in kinds and b in kinds
    ]
    n_spans = sum(len(t.spans) for t in traces)
    completeness = 1.0
    if n_spans:
        completeness = max(0.0, 1.0 - (missing_parent / n_spans) - (unknown_n / n_spans))
    trust = TrustLevel.MEDIUM
    if completeness >= 0.9 and unknown_n == 0 and not any(n.mixed for n in nodes):
        trust = TrustLevel.HIGH
    elif completeness < 0.2:
        trust = TrustLevel.UNTRUSTED
        warnings.append("graph completeness below 0.2")
    elif completeness < 0.5 or unknown_n > n_spans / 2:
        trust = TrustLevel.LOW
        warnings.append("graph completeness below 0.5 or many unknown ops")
    ident_src = json.dumps(
        {"nodes": [n.node_id for n in nodes], "edges": [(e.src, e.dst, e.kind.value) for e in edges]},
        sort_keys=True,
    )
    identity = hashlib.sha256(ident_src.encode()).hexdigest()[:16]
    commitment = tuple(
        n.node_id for n in nodes if n.is_decision and not n.side_effects
    )
    return ArchitectureGraph(
        version=SCHEMA_VERSION,
        identity=identity,
        nodes=nodes,
        edges=edges,
        completeness=round(completeness, 4),
        trust=trust,
        warnings=tuple(warnings),
        commitment_node_ids=commitment,
    )
