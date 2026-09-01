from __future__ import annotations

from superdeterminism.graph import reconstruct
from superdeterminism.models import EdgeKind, NodeKind, Span, Trace, TrustLevel


def test_parent_child_edge_and_commitment() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "agent"},
                    span_id="1",
                    output={"ok": True},
                ),
                Span(
                    name="execute_tool t",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "lookup_order",
                    },
                    span_id="2",
                    parent_span_id="1",
                    output={"id": 1},
                ),
            ],
            trace_id="t0",
        )
    ]
    graph = reconstruct(traces)
    assert any(e.src == "agent" and e.dst == "lookup_order" and e.kind is EdgeKind.PARENT for e in graph.edges)
    assert "agent" in graph.commitment_node_ids
    assert "lookup_order" not in graph.commitment_node_ids
    assert graph.trust is TrustLevel.HIGH
    assert graph.completeness >= 0.9


def test_control_and_handoff_edges() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={
                        "gen_ai.operation.name": "chat",
                        "langgraph_node": "router",
                        "langgraph_triggers": ["refund_agent"],
                    },
                    span_id="r",
                ),
                Span(
                    name="execute_tool transfer_to_refund_agent",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "transfer_to_refund_agent",
                    },
                    span_id="h",
                    parent_span_id="r",
                ),
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "refund_agent"},
                    span_id="a",
                    parent_span_id="h",
                ),
            ]
        )
    ]
    graph = reconstruct(traces)
    kinds = {e.kind for e in graph.edges}
    assert EdgeKind.CONTROL in kinds
    assert EdgeKind.HANDOFF in kinds
    assert any(n.node_id == "transfer_to_refund_agent" and n.node_kind is NodeKind.ROUTER for n in graph.nodes)


def test_missing_parents_lower_completeness() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="mystery",
                    attributes={"gen_ai.operation.name": "not_a_real_op"},
                    span_id="x",
                    parent_span_id="missing",
                )
            ]
        )
    ]
    graph = reconstruct(traces)
    assert graph.completeness < 0.5
    assert graph.trust in {TrustLevel.LOW, TrustLevel.UNTRUSTED}
