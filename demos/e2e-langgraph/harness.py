#!/usr/bin/env python3
"""Run a LangGraph research-assistant-shaped agent and emit Unagent traces.

Topology mirrors JoshuaC215/agent-service-toolkit research_assistant:
  guard_input → model ⇄ tools | block_unsafe_content

ponytail: FakeMessagesListChatModel so CI/cloud needs no API keys;
graph + ToolNode are real LangGraph.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import uuid
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

OUT_DEFAULT = Path(__file__).resolve().parent / "traces.json"
N_DEFAULT = 40


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    safety: str


@tool
def calculator(expression: str) -> str:
    """Evaluate a simple math expression (numexpr-style subset)."""
    expr = expression.strip()
    if not re.fullmatch(r"[0-9+\-*/(). eE]+", expr):
        raise ValueError(f"unsupported expression: {expr!r}")
    # ponytail: stdlib eval with empty builtins — upgrade to numexpr if parity matters
    value = eval(expr, {"__builtins__": {}}, {"pi": math.pi, "e": math.e})  # noqa: S307
    return str(value)


TOOLS = [calculator]


def _fake_guard() -> FakeMessagesListChatModel:
    # Stable structured safety verdict → FlipToDet candidate under L0
    return FakeMessagesListChatModel(
        responses=[
            AIMessage(content=json.dumps({"safety": "safe", "categories": []})),
        ]
    )


def _fake_model_tool_then_answer(expression: str, result: str) -> FakeMessagesListChatModel:
    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "calculator",
                "args": {"expression": expression},
                "id": "call_calc",
                "type": "tool_call",
            }
        ],
    )
    final = AIMessage(content=f"The result of {expression} is {result}.")
    return FakeMessagesListChatModel(responses=[tool_call, final])


def build_graph(model: FakeMessagesListChatModel, guard: FakeMessagesListChatModel):
    def guard_input(state: AgentState) -> dict:
        verdict_msg = guard.invoke(state["messages"])
        raw = str(verdict_msg.content)
        try:
            parsed = json.loads(raw)
            safety = "unsafe" if parsed.get("safety") == "unsafe" else "safe"
        except json.JSONDecodeError:
            safety = "safe"
        return {"safety": safety, "messages": [verdict_msg]}

    def call_model(state: AgentState) -> dict:
        # ponytail: FakeMessagesListChatModel has no bind_tools; tool_calls are scripted
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    def block_unsafe_content(_state: AgentState) -> dict:
        return {"messages": [AIMessage(content="Blocked: conversation flagged as unsafe.")]}

    def route_safety(state: AgentState) -> Literal["model", "block_unsafe_content"]:
        return "block_unsafe_content" if state.get("safety") == "unsafe" else "model"

    def route_model(state: AgentState) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "__end__"

    g = StateGraph(AgentState)
    g.add_node("guard_input", guard_input)
    g.add_node("model", call_model)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_node("block_unsafe_content", block_unsafe_content)
    g.add_edge(START, "guard_input")
    g.add_conditional_edges(
        "guard_input",
        route_safety,
        {"model": "model", "block_unsafe_content": "block_unsafe_content"},
    )
    g.add_conditional_edges(
        "model",
        route_model,
        {"tools": "tools", "__end__": END},
    )
    g.add_edge("tools", "model")
    g.add_edge("block_unsafe_content", END)
    return g.compile()


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
) -> dict:
    attrs: dict = {
        "gen_ai.operation.name": op,
        "langgraph_node": node,
        "gen_ai.request.model": "fake-list",
    }
    if triggers:
        attrs["langgraph_triggers"] = triggers
    if tool_name:
        attrs["gen_ai.tool.name"] = tool_name
    span = {
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


def run_once(expression: str = "300 * 200") -> dict:
    """Execute one graph run; return a single Unagent trace dict."""
    result = str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    guard = _fake_guard()
    model = _fake_model_tool_then_answer(expression, result)
    app = build_graph(model, guard)

    root = uuid.uuid4().hex[:16]
    spans: list[dict] = [
        _span(
            name="guard_input",
            node="guard_input",
            op="chat",
            span_id=root,
            parent=None,
            inp={"text": f"What is {expression}?"},
            out={"safety": "safe", "categories": []},
            tokens=24,
            latency_ms=40,
            triggers=["model", "block_unsafe_content"],
        )
    ]

    final_state = app.invoke(
        {
            "messages": [HumanMessage(content=f"What is {expression}?")],
            "safety": "",
        }
    )

    model_1 = uuid.uuid4().hex[:16]
    spans.append(
        _span(
            name="chat fake-list",
            node="model",
            op="chat",
            span_id=model_1,
            parent=root,
            inp={"text": f"What is {expression}?"},
            out={"tool_calls": [{"name": "calculator", "args": {"expression": expression}}]},
            tokens=80,
            latency_ms=120,
            triggers=["tools", "__end__"],
        )
    )
    tool_id = uuid.uuid4().hex[:16]
    spans.append(
        _span(
            name="execute_tool calculator",
            node="tools",
            op="execute_tool",
            span_id=tool_id,
            parent=model_1,
            inp={"expression": expression},
            out={"result": result},
            tokens=0,
            latency_ms=5,
            tool_name="calculator",
        )
    )
    model_2 = uuid.uuid4().hex[:16]
    last = final_state["messages"][-1]
    content = getattr(last, "content", str(last))
    spans.append(
        _span(
            name="chat fake-list",
            node="model",
            op="chat",
            span_id=model_2,
            parent=tool_id,
            inp={"tool_result": result},
            out={"text": content},
            tokens=60,
            latency_ms=100,
            triggers=["__end__"],
        )
    )
    return {"spans": spans}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=N_DEFAULT, help="number of graph runs")
    p.add_argument("--out", type=Path, default=OUT_DEFAULT)
    p.add_argument("--expression", default="300 * 200")
    args = p.parse_args(argv)

    # Smoke one live invoke before bulk emit (fails fast if LangGraph breaks)
    smoke = run_once(args.expression)
    assert smoke["spans"], "harness produced empty spans"

    traces = [run_once(args.expression) for _ in range(args.n)]
    payload = {"traces": traces}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({args.n} traces)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
