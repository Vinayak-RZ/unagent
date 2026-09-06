"""Nest flat inspect graph into L0 → L1 → L2 Studio subgraphs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from superdeterminism.classify import classify_span
from superdeterminism.models import Trace

_LAYER_ATTR = "advisor.layer"
_PARENT_AGENT_ATTR = "advisor.parent_agent"


def _layers_from_traces(traces: list[Trace]) -> dict[str, str]:
    layers: dict[str, str] = {}
    for trace in traces:
        for span in trace.spans:
            node_id, _, _ = classify_span(span)
            layer = span.attributes.get(_LAYER_ATTR)
            if layer:
                layers[node_id] = str(layer)
    return layers


def _parent_agents_from_traces(traces: list[Trace]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for trace in traces:
        for span in trace.spans:
            node_id, _, _ = classify_span(span)
            parent = span.attributes.get(_PARENT_AGENT_ATTR)
            if parent:
                owners[node_id] = str(parent)
    return owners


def _node_dict(n: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    out = {
        "node_id": n["node_id"],
        "node_kind": n.get("node_kind"),
        "det_class": n.get("det_class"),
        "mixed": n.get("mixed"),
        "side_effects": n.get("side_effects"),
        "is_decision": n.get("is_decision"),
    }
    if extra:
        out.update(extra)
    return out


def nest_for_studio(
    flat_nodes: list[dict[str, Any]],
    flat_edges: list[dict[str, Any]],
    traces: list[Trace],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (root_nodes, root_edges) with nested subgraph on L0/L1 nodes."""
    layers = _layers_from_traces(traces)
    owners = _parent_agents_from_traces(traces)
    by_id = {n["node_id"]: n for n in flat_nodes}

    l0 = [n for n in flat_nodes if layers.get(n["node_id"]) == "L0"]
    l1 = [n for n in flat_nodes if layers.get(n["node_id"]) == "L1"]
    l2 = [n for n in flat_nodes if layers.get(n["node_id"]) == "L2"]

    if not l0 and not l1:
        return flat_nodes, flat_edges

    l1_ids = {n["node_id"] for n in l1}
    l2_by_agent: dict[str, list[dict]] = defaultdict(list)
    for n in l2:
        agent = owners.get(n["node_id"], "")
        if agent:
            l2_by_agent[agent].append(_node_dict(n))

    l1_nested: list[dict] = []
    for n in l1:
        children = l2_by_agent.get(n["node_id"], [])
        spec = _node_dict(n, {"advisor_layer": "L1"})
        if children:
            child_edges = [
                {"src": children[i]["node_id"], "dst": children[i + 1]["node_id"], "kind": "parent"}
                for i in range(len(children) - 1)
            ]
            spec["subgraph"] = {"nodes": children, "edges": child_edges}
        l1_nested.append(spec)

    root_nodes: list[dict] = []
    for n in l0:
        spec = _node_dict(n, {"advisor_layer": "L0"})
        l1_edges = [
            e for e in flat_edges if e["src"] == n["node_id"] and e["dst"] in l1_ids
        ]
        if l1_nested:
            spec["subgraph"] = {
                "nodes": l1_nested,
                "edges": l1_edges or [
                    {"src": a["node_id"], "dst": b["node_id"], "kind": "handoff"}
                    for a in l1_nested
                    for b in l1_nested
                    if a["node_id"] != b["node_id"]
                ][: len(l1_nested)],
            }
        root_nodes.append(spec)

    if not root_nodes:
        root_nodes = l1_nested if l1_nested else flat_nodes

    root_ids = {n["node_id"] for n in root_nodes}
    root_edges = [e for e in flat_edges if e["src"] in root_ids and e["dst"] in root_ids]
    return root_nodes, root_edges
