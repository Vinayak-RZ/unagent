"""Tests for hierarchical Studio graph nesting."""

from __future__ import annotations

import json

from superdeterminism.graph_hierarchy import nest_for_studio
from superdeterminism.ingest import load_traces_path
from superdeterminism.pipeline import inspect_traces


def test_nest_for_studio_subgraph_on_l0(tmp_path) -> None:
    trace_file = tmp_path / "t.json"
    trace_file.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "task_router",
                                "span_id": "a1",
                                "attributes": {
                                    "gen_ai.operation.name": "chat",
                                    "langgraph_node": "task_router",
                                    "advisor.layer": "L0",
                                },
                                "input": {},
                                "output": {"route": "research_agent"},
                            },
                            {
                                "name": "research_agent",
                                "span_id": "a2",
                                "parent_span_id": "a1",
                                "attributes": {
                                    "gen_ai.operation.name": "chat",
                                    "langgraph_node": "research_agent",
                                    "advisor.layer": "L1",
                                    "advisor.parent_agent": "research_agent",
                                },
                                "input": {},
                                "output": {},
                            },
                            {
                                "name": "web_search",
                                "span_id": "a3",
                                "parent_span_id": "a2",
                                "attributes": {
                                    "gen_ai.operation.name": "execute_tool",
                                    "langgraph_node": "web_search",
                                    "gen_ai.tool.name": "web_search",
                                    "advisor.layer": "L2",
                                    "advisor.parent_agent": "research_agent",
                                },
                                "input": {},
                                "output": {"result": "ok"},
                            },
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    traces = load_traces_path(trace_file)
    inspected = inspect_traces(traces)
    root_nodes, _root_edges = nest_for_studio(inspected["nodes"], inspected["edges"], traces)
    assert len(root_nodes) == 1
    router = root_nodes[0]
    assert router["node_id"] == "task_router"
    assert router.get("subgraph")
    l1_ids = {n["node_id"] for n in router["subgraph"]["nodes"]}
    assert "research_agent" in l1_ids
    research = next(n for n in router["subgraph"]["nodes"] if n["node_id"] == "research_agent")
    assert research.get("subgraph")
    l2_ids = {n["node_id"] for n in research["subgraph"]["nodes"]}
    assert "web_search" in l2_ids
