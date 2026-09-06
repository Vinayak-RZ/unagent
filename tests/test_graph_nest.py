from __future__ import annotations

from superdeterminism.classify import classify_span
from superdeterminism.graph import nest_for_studio, reconstruct, story_events_from_traces
from superdeterminism.models import NodeKind, Span, Trace


def _span(name: str, attrs: dict, span_id: str, parent: str = "") -> Span:
    return Span(name=name, attributes=attrs, span_id=span_id, parent_span_id=parent)


def _multiagent_trace() -> list[Trace]:
    return [
        Trace(
            spans=[
                _span(
                    "wf",
                    {"gen_ai.operation.name": "invoke_workflow", "langgraph_node": "delivery_orchestrator"},
                    "w",
                ),
                _span(
                    "chat",
                    {"gen_ai.operation.name": "chat", "langgraph_node": "supervisor"},
                    "s",
                    "w",
                ),
                _span(
                    "handoff",
                    {
                        "gen_ai.operation.name": "execute_tool",
                        "langgraph_node": "handoff",
                        "gen_ai.tool.name": "transfer_to_research_agent",
                    },
                    "h",
                    "s",
                ),
                _span(
                    "invoke",
                    {"gen_ai.operation.name": "invoke_agent", "langgraph_node": "research_agent"},
                    "a",
                    "h",
                ),
                _span(
                    "chat",
                    {"gen_ai.operation.name": "chat", "langgraph_node": "researcher"},
                    "r",
                    "a",
                ),
                _span(
                    "search",
                    {
                        "gen_ai.operation.name": "retrieval",
                        "langgraph_node": "web_search",
                        "gen_ai.tool.name": "web_search",
                        "advisor.surface": "mcp",
                    },
                    "t",
                    "r",
                ),
            ]
        )
    ]


def test_transfer_to_research_agent_is_router_not_retriever() -> None:
    nid, kind, _ = classify_span(
        _span(
            "execute_tool",
            {
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": "transfer_to_research_agent",
                "langgraph_node": "handoff",
            },
            "h",
        )
    )
    assert nid == "handoff"
    assert kind is NodeKind.ROUTER


def test_nest_puts_tools_inside_subagent() -> None:
    traces = _multiagent_trace()
    graph = reconstruct(traces)
    nested = nest_for_studio(graph, traces)
    root_ids = {n["node_id"] for n in nested["nodes"]}
    assert "research_agent" in root_ids
    assert "supervisor" in root_ids
    assert "delivery_orchestrator" in root_ids
    assert "web_search" not in root_ids
    assert "researcher" not in root_ids
    agent = next(n for n in nested["nodes"] if n["node_id"] == "research_agent")
    inner = {n["node_id"] for n in agent["subgraph"]["nodes"]}
    assert inner == {"researcher", "web_search"}
    search = next(n for n in agent["subgraph"]["nodes"] if n["node_id"] == "web_search")
    assert search["surface"] == "mcp"


def test_nest_does_not_change_flat_identity() -> None:
    traces = _multiagent_trace()
    a = reconstruct(traces)
    b = reconstruct(traces)
    nest_for_studio(a, traces)
    assert a.identity == b.identity


def test_story_events_start_at_orchestrator() -> None:
    events = story_events_from_traces(_multiagent_trace())
    assert events[0]["node_id"] == "delivery_orchestrator"
    assert any(e["node_id"] == "web_search" for e in events)
