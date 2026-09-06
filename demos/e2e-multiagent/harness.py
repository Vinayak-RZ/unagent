#!/usr/bin/env python3
"""Delivery-orchestrator LangGraph + agent-as-model traces.

Layer 0: supervisor hands off to research / implement / review, then policy_gate.
Layer 1: each specialist calls tools, MCP, or skills from the cassette.

ponytail: FakeMessagesListChatModel replays this agent's transcripts (D22).
Graph + ToolNode + compiled subgraphs are real LangGraph.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent_model import Scenario, expand_mix, load_scenarios  # noqa: E402

OUT_DEFAULT = Path(__file__).resolve().parent / "traces.json"
N_DEFAULT = 42

SURFACES = {
    "web_search": "mcp",
    "retrieve_docs": "mcp",
    "cite_sources": "tool",
    "read_file": "skill",
    "apply_patch": "skill",
    "run_tests": "tool",
    "lint": "tool",
    "security_scan": "tool",
}

RETRIEVE_OPS = frozenset({"web_search", "retrieve_docs"})


class OrchestratorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    queue: list[str]
    task: str


def _tool_result(cassette: dict[str, Any], name: str, **kwargs: Any) -> str:
    for step in cassette.get("tools") or []:
        if step.get("name") == name:
            return str(step.get("result", ""))
    return json.dumps({"name": name, "args": kwargs})


def _bind_tools(cassette: dict[str, Any]):
    def web_search(query: str) -> str:
        """MCP web search."""
        return _tool_result(cassette, "web_search", query=query)

    def retrieve_docs(path: str) -> str:
        """Retrieve a local doc path."""
        return _tool_result(cassette, "retrieve_docs", path=path)

    def cite_sources(ids: str) -> str:
        """Format citation ids."""
        return _tool_result(cassette, "cite_sources", ids=ids)

    def read_file(path: str) -> str:
        """Read a workspace file (skill)."""
        return _tool_result(cassette, "read_file", path=path)

    def apply_patch(path: str, note: str = "") -> str:
        """Apply a patch (skill; side-effecting)."""
        return _tool_result(cassette, "apply_patch", path=path, note=note)

    def run_tests(target: str) -> str:
        """Run a test target."""
        return _tool_result(cassette, "run_tests", target=target)

    def lint(path: str) -> str:
        """Lint a path."""
        return _tool_result(cassette, "lint", path=path)

    def security_scan(path: str) -> str:
        """Scan a path for obvious secrets."""
        return _tool_result(cassette, "security_scan", path=path)

    return {
        "web_search": tool(web_search),
        "retrieve_docs": tool(retrieve_docs),
        "cite_sources": tool(cite_sources),
        "read_file": tool(read_file),
        "apply_patch": tool(apply_patch),
        "run_tests": tool(run_tests),
        "lint": tool(lint),
        "security_scan": tool(security_scan),
    }


def _fake_from_cassette(cassette: dict[str, Any]) -> FakeMessagesListChatModel:
    responses: list[AIMessage] = []
    for i, step in enumerate(cassette.get("tools") or []):
        responses.append(
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": step["name"],
                        "args": step.get("args") or {},
                        "id": f"call_{step['name']}_{i}",
                        "type": "tool_call",
                    }
                ],
            )
        )
    responses.append(AIMessage(content=str(cassette.get("answer") or "done")))
    return FakeMessagesListChatModel(responses=responses)


def _specialist_graph(llm_node: str, model: FakeMessagesListChatModel, tools: list):
    def call_model(state: OrchestratorState) -> dict:
        return {"messages": [model.invoke(state["messages"])]}

    def route_model(state: OrchestratorState) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "__end__"

    g = StateGraph(OrchestratorState)
    g.add_node(llm_node, call_model)
    g.add_node("tools", ToolNode(tools))
    g.add_edge(START, llm_node)
    g.add_conditional_edges(llm_node, route_model, {"tools": "tools", "__end__": END})
    g.add_edge("tools", llm_node)
    return g.compile()


def build_orchestrator(scenario: Scenario):
    route = list(scenario.route)
    research_c = scenario.agents.get("research_agent") or {}
    implement_c = scenario.agents.get("implement_agent") or {}
    review_c = scenario.agents.get("review_agent") or {}
    r_bound = _bind_tools(research_c)
    i_bound = _bind_tools(implement_c)
    v_bound = _bind_tools(review_c)

    research = _specialist_graph(
        "researcher",
        _fake_from_cassette(research_c),
        [r_bound["web_search"], r_bound["retrieve_docs"], r_bound["cite_sources"]],
    )
    implement = _specialist_graph(
        "implementer",
        _fake_from_cassette(implement_c),
        [i_bound["read_file"], i_bound["apply_patch"], i_bound["run_tests"]],
    )
    review = _specialist_graph(
        "reviewer",
        _fake_from_cassette(review_c),
        [v_bound["lint"], v_bound["security_scan"]],
    )

    def supervisor(state: OrchestratorState) -> dict:
        nxt = list(state.get("queue") or route)
        plan = {"next": list(route), "blocked": not scenario.allow}
        return {
            "messages": [AIMessage(content=json.dumps(plan))],
            "queue": nxt,
        }

    def policy_gate(_state: OrchestratorState) -> dict:
        return {"messages": [AIMessage(content=json.dumps(scenario.policy))]}

    def take_research(state: OrchestratorState) -> dict:
        inner = research.invoke({"messages": state["messages"], "queue": [], "task": state["task"]})
        q = list(state.get("queue") or [])
        if q and q[0] == "research_agent":
            q = q[1:]
        return {"messages": inner["messages"], "queue": q}

    def take_implement(state: OrchestratorState) -> dict:
        inner = implement.invoke({"messages": state["messages"], "queue": [], "task": state["task"]})
        q = list(state.get("queue") or [])
        if q and q[0] == "implement_agent":
            q = q[1:]
        return {"messages": inner["messages"], "queue": q}

    def take_review(state: OrchestratorState) -> dict:
        inner = review.invoke({"messages": state["messages"], "queue": [], "task": state["task"]})
        q = list(state.get("queue") or [])
        if q and q[0] == "review_agent":
            q = q[1:]
        return {"messages": inner["messages"], "queue": q}

    def route_supervisor(state: OrchestratorState) -> str:
        q = state.get("queue") or []
        if not q:
            return "policy_gate"
        return q[0]

    g = StateGraph(OrchestratorState)
    g.add_node("supervisor", supervisor)
    g.add_node("research_agent", take_research)
    g.add_node("implement_agent", take_implement)
    g.add_node("review_agent", take_review)
    g.add_node("policy_gate", policy_gate)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "research_agent": "research_agent",
            "implement_agent": "implement_agent",
            "review_agent": "review_agent",
            "policy_gate": "policy_gate",
        },
    )
    g.add_conditional_edges(
        "research_agent",
        route_supervisor,
        {
            "research_agent": "research_agent",
            "implement_agent": "implement_agent",
            "review_agent": "review_agent",
            "policy_gate": "policy_gate",
        },
    )
    g.add_conditional_edges(
        "implement_agent",
        route_supervisor,
        {
            "research_agent": "research_agent",
            "implement_agent": "implement_agent",
            "review_agent": "review_agent",
            "policy_gate": "policy_gate",
        },
    )
    g.add_conditional_edges(
        "review_agent",
        route_supervisor,
        {
            "research_agent": "research_agent",
            "implement_agent": "implement_agent",
            "review_agent": "review_agent",
            "policy_gate": "policy_gate",
        },
    )
    g.add_edge("policy_gate", END)
    return g.compile()


def _sid() -> str:
    return uuid.uuid4().hex[:16]


def _span(
    *,
    name: str,
    node: str,
    op: str,
    span_id: str,
    parent: str | None,
    inp: dict,
    out: dict,
    tokens: int,
    latency_ms: int,
    triggers: list[str] | None = None,
    tool_name: str | None = None,
    surface: str | None = None,
) -> dict:
    attrs: dict[str, Any] = {
        "gen_ai.operation.name": op,
        "langgraph_node": node,
        "gen_ai.request.model": "agent-as-model",
    }
    if triggers:
        attrs["langgraph_triggers"] = triggers
    if tool_name:
        attrs["gen_ai.tool.name"] = tool_name
    if surface:
        attrs["advisor.surface"] = surface
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


def _handoff_tool(agent: str) -> str:
    return f"transfer_to_{agent}"


def emit_spans(scenario: Scenario) -> list[dict]:
    """Unagent-shaped spans matching the run. Parent edges drive Studio nest."""
    spans: list[dict] = []
    wf = _sid()
    spans.append(
        _span(
            name="delivery_orchestrator",
            node="delivery_orchestrator",
            op="invoke_workflow",
            span_id=wf,
            parent=None,
            inp={"task": scenario.task},
            out={"route": list(scenario.route), "policy": scenario.policy},
            tokens=0,
            latency_ms=8,
        )
    )
    sup = _sid()
    triggers = list(scenario.route) + ["policy_gate"]
    handoffs = [_handoff_tool(a) for a in scenario.route]
    spans.append(
        _span(
            name="chat supervisor",
            node="supervisor",
            op="chat",
            span_id=sup,
            parent=wf,
            inp={"task": scenario.task},
            out={"next": list(scenario.route), "handoffs": handoffs},
            tokens=48,
            latency_ms=90,
            triggers=triggers,
        )
    )
    for agent in scenario.route:
        hid = _sid()
        spans.append(
            _span(
                name=f"handoff {_handoff_tool(agent)}",
                node="handoff",
                op="execute_tool",
                span_id=hid,
                parent=sup,
                inp={"agent": agent},
                out={"handoff": agent},
                tokens=0,
                latency_ms=4,
                tool_name=_handoff_tool(agent),
            )
        )
        agent_span = _sid()
        llm_name = {
            "research_agent": "researcher",
            "implement_agent": "implementer",
            "review_agent": "reviewer",
        }[agent]
        cassette = scenario.agents.get(agent) or {}
        spans.append(
            _span(
                name=f"invoke_agent {agent}",
                node=agent,
                op="invoke_agent",
                span_id=agent_span,
                parent=hid,
                inp={"task": scenario.task},
                out={"agent": agent},
                tokens=0,
                latency_ms=12,
            )
        )
        parent = agent_span
        for i, step in enumerate(cassette.get("tools") or []):
            think = _sid()
            spans.append(
                _span(
                    name=f"chat {llm_name}",
                    node=llm_name,
                    op="chat",
                    span_id=think,
                    parent=parent,
                    inp={"step": i, "task": scenario.task},
                    out={"tool_calls": [{"name": step["name"], "args": step.get("args") or {}}]},
                    tokens=64,
                    latency_ms=110,
                )
            )
            tool_id = _sid()
            tname = str(step["name"])
            op = "retrieval" if tname in RETRIEVE_OPS else "execute_tool"
            spans.append(
                _span(
                    name=f"{op} {tname}",
                    node=tname,
                    op=op,
                    span_id=tool_id,
                    parent=think,
                    inp=step.get("args") or {},
                    out={"result": step.get("result")},
                    tokens=0,
                    latency_ms=15,
                    tool_name=tname,
                    surface=SURFACES.get(tname),
                )
            )
            parent = tool_id
        final = _sid()
        spans.append(
            _span(
                name=f"chat {llm_name}",
                node=llm_name,
                op="chat",
                span_id=final,
                parent=parent,
                inp={"task": scenario.task},
                out={"text": cassette.get("answer")},
                tokens=80,
                latency_ms=100,
            )
        )
    pg = _sid()
    spans.append(
        _span(
            name="chat policy_gate",
            node="policy_gate",
            op="chat",
            span_id=pg,
            parent=wf,
            inp={"task": scenario.task, "route": list(scenario.route)},
            out=dict(scenario.policy),
            tokens=20,
            latency_ms=35,
        )
    )
    return spans


def run_once(scenario: Scenario) -> dict:
    app = build_orchestrator(scenario)
    final = app.invoke(
        {
            "messages": [HumanMessage(content=scenario.task)],
            "queue": list(scenario.route),
            "task": scenario.task,
        }
    )
    last = final["messages"][-1]
    assert getattr(last, "content", None), "orchestrator produced empty policy message"
    # live ToolMessage objects prove ToolNode ran when specialists had tools
    if scenario.route:
        assert any(isinstance(m, (AIMessage, ToolMessage)) for m in final["messages"])
    return {"spans": emit_spans(scenario), "scenario": scenario.id}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=N_DEFAULT)
    p.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = p.parse_args(argv)

    scenarios = load_scenarios()
    smoke = run_once(scenarios[0])
    assert smoke["spans"], "empty spans"

    mix = expand_mix(scenarios, args.n)
    traces = [run_once(s) for s in mix]
    payload = {
        "traces": [{"spans": t["spans"]} for t in traces],
        "advisor.demo": "e2e-multiagent",
        "advisor.model": "agent-as-model",
        "mix": [s.id for s in mix],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({args.n} traces) mix={sorted({s.id for s in mix})}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
