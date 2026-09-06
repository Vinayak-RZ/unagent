#!/usr/bin/env python3
"""Multi-layer orchestrator demo: L0 supervisor → L1 agents → L2 tools/MCPs/skills.

ponytail: span emitter (no live API keys); LangGraph smoke optional via --smoke-graph.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

OUT_DEFAULT = Path(__file__).resolve().parent / "traces.json"
N_DEFAULT = 40
WRONG_ROUTE_INDICES = {7, 23}

AGENT_TOOLS: dict[str, list[str]] = {
    "research_agent": ["web_search", "mcp_arxiv", "skill_docs"],
    "code_agent": ["code_exec", "skill_lint"],
    "data_agent": ["sql_query", "mcp_warehouse"],
}

L2_KIND: dict[str, str] = {
    "web_search": "tool",
    "mcp_arxiv": "mcp",
    "skill_docs": "skill",
    "code_exec": "tool",
    "skill_lint": "skill",
    "sql_query": "tool",
    "mcp_warehouse": "mcp",
}


def _load_scenarios(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("scenarios") or [])


def _span(
    *,
    name: str,
    node: str,
    op: str,
    layer: str,
    span_id: str,
    parent: str | None,
    inp: dict,
    out: dict,
    tokens: int,
    latency_ms: int,
    parent_agent: str | None = None,
    triggers: list[str] | None = None,
    tool_name: str | None = None,
    mcp_namespace: str | None = None,
    skill_id: str | None = None,
) -> dict:
    attrs: dict[str, Any] = {
        "gen_ai.operation.name": op,
        "langgraph_node": node,
        "advisor.layer": layer,
        "gen_ai.request.model": "fake-list",
    }
    if parent_agent:
        attrs["advisor.parent_agent"] = parent_agent
    if triggers:
        attrs["langgraph_triggers"] = triggers
    if tool_name:
        attrs["gen_ai.tool.name"] = tool_name
    if mcp_namespace:
        attrs["advisor.mcp_namespace"] = mcp_namespace
    if skill_id:
        attrs["advisor.skill_id"] = skill_id
    span: dict[str, Any] = {
        "name": name,
        "attributes": attrs,
        "input": inp,
        "output": out,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "error": False,
        "span_id": span_id,
    }
    if parent:
        span["parent_span_id"] = parent
    return span


def _stable_route_output(route: str, query: str) -> dict:
    return {"route": route, "confidence": 0.95, "intent_summary": query[:80]}


def run_once(scenario: dict[str, Any], run_idx: int) -> dict:
    """Emit one trace with L0→L1→L2 parentage."""
    query = str(scenario["query"])
    route = str(scenario["route"])
    if run_idx in WRONG_ROUTE_INDICES and scenario.get("misroute"):
        route = "code_agent" if route == "research_agent" else route

    tool = str(scenario.get("tool") or AGENT_TOOLS.get(route, ["web_search"])[0])
    root = uuid.uuid4().hex[:16]
    gate_span = uuid.uuid4().hex[:16]
    spans: list[dict] = [
        _span(
            name="supervisor_gate",
            node="supervisor_gate",
            op="chat",
            layer="L0",
            span_id=gate_span,
            parent=None,
            inp={"query": query},
            out={"status": "ok", "policy_version": 1, "orchestration": "supervisor"},
            tokens=12,
            latency_ms=8,
            triggers=["task_router"],
        ),
        _span(
            name="task_router",
            node="task_router",
            op="chat",
            layer="L0",
            span_id=root,
            parent=gate_span,
            inp={"query": query},
            out=_stable_route_output(route, query),
            tokens=32,
            latency_ms=35,
            triggers=[route],
        ),
    ]

    agent_span = uuid.uuid4().hex[:16]
    divergent = route == "research_agent" and (run_idx % 4 == 3)
    if divergent:
        spans.append(
            _span(
                name=f"chat {route}",
                node=route,
                op="chat",
                layer="L1",
                span_id=agent_span,
                parent=root,
                parent_agent=route,
                inp={"query": query},
                out={"text": f"Direct answer for: {query}"},
                tokens=55,
                latency_ms=90,
                triggers=["__end__"],
            )
        )
    else:
        tool_span = uuid.uuid4().hex[:16]
        l2_kind = L2_KIND.get(tool, "tool")
        mcp_ns = tool.replace("mcp_", "") if tool.startswith("mcp_") else None
        skill = tool if tool.startswith("skill_") else None
        spans.append(
            _span(
                name=f"chat {route}",
                node=route,
                op="chat",
                layer="L1",
                span_id=agent_span,
                parent=root,
                parent_agent=route,
                inp={"query": query},
                out={"tool_calls": [{"name": tool, "args": {"query": query}}]},
                tokens=70,
                latency_ms=110,
                triggers=[tool],
            )
        )
        spans.append(
            _span(
                name=f"execute_tool {tool}",
                node=tool,
                op="execute_tool",
                layer="L2",
                span_id=tool_span,
                parent=agent_span,
                parent_agent=route,
                inp={"query": query},
                out={"result": f"stub result for {tool}"},
                tokens=0,
                latency_ms=8 if l2_kind == "tool" else 25,
                tool_name=tool if l2_kind == "tool" else None,
                mcp_namespace=mcp_ns,
                skill_id=skill,
            )
        )
        final_span = uuid.uuid4().hex[:16]
        spans.append(
            _span(
                name=f"chat {route}",
                node=route,
                op="chat",
                layer="L1",
                span_id=final_span,
                parent=tool_span,
                parent_agent=route,
                inp={"tool_result": "stub"},
                out={"text": f"Synthesized answer for: {query}"},
                tokens=48,
                latency_ms=85,
                triggers=["__end__"],
            )
        )

    return {"spans": spans}


def _scenario_for_index(scenarios: list[dict], idx: int) -> dict:
    if not scenarios:
        return {"query": "default", "route": "research_agent", "tool": "web_search"}
    weights = [3, 3, 2, 2, 2, 2, 1]
    pool: list[dict] = []
    for i, sc in enumerate(scenarios):
        pool.extend([sc] * weights[min(i, len(weights) - 1)])
    return pool[idx % len(pool)]


def smoke_langgraph() -> None:
    """Optional: verify LangGraph import path for CI extras matrix."""
    import langgraph  # noqa: F401


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=N_DEFAULT)
    p.add_argument("--out", type=Path, default=OUT_DEFAULT)
    p.add_argument(
        "--scenarios",
        type=Path,
        default=Path(__file__).resolve().parent / "scenarios.json",
    )
    p.add_argument("--smoke-graph", action="store_true")
    args = p.parse_args(argv)

    if args.smoke_graph:
        smoke_langgraph()

    scenarios = _load_scenarios(args.scenarios)
    smoke = run_once(scenarios[0] if scenarios else {}, 0)
    assert smoke["spans"], "harness produced empty spans"

    traces = [run_once(_scenario_for_index(scenarios, i), i) for i in range(args.n)]
    payload = {"traces": traces}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({args.n} traces)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
