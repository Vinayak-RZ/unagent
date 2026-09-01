"""Span → node_id, node_kind, det.class. No framework imports."""

from __future__ import annotations

from superdeterminism.models import DetClass, NodeKind, Span

_OP_TO_KIND = {
    "chat": NodeKind.LLM_REASONER,
    "generate_content": NodeKind.LLM_REASONER,
    "text_completion": NodeKind.LLM_REASONER,
    "plan": NodeKind.LLM_REASONER,
    "execute_tool": NodeKind.DETERMINISTIC_TOOL,
    "invoke_agent": NodeKind.SUBAGENT,
    "create_agent": NodeKind.SUBAGENT,
    "invoke_workflow": NodeKind.WORKFLOW,
    "retrieval": NodeKind.RETRIEVER,
    "search_memory": NodeKind.RETRIEVER,
}


def _attr_get(attrs: dict, *keys: str):
    for key in keys:
        if key in attrs and attrs[key] not in (None, ""):
            return attrs[key]
    return None


def classify_span(span: Span) -> tuple[str, NodeKind, DetClass]:
    attrs = span.attributes
    op = str(_attr_get(attrs, "gen_ai.operation.name", "gen_ai.operation") or "").lower()
    tool = _attr_get(attrs, "gen_ai.tool.name")
    node_id = str(
        _attr_get(attrs, "langgraph_node", "gen_ai.agent.name", "gen_ai.tool.name")
        or span.name
    )
    kind = _OP_TO_KIND.get(op, NodeKind.UNKNOWN)
    if kind == NodeKind.UNKNOWN:
        name = span.name.lower()
        if name.startswith("execute_tool") or name.endswith("_tool"):
            kind = NodeKind.DETERMINISTIC_TOOL
        elif name.startswith("chat") or name.startswith("llm"):
            kind = NodeKind.LLM_REASONER
        elif "retriev" in name:
            kind = NodeKind.RETRIEVER
        elif name.startswith("agent") or name.endswith("_agent"):
            kind = NodeKind.SUBAGENT
        elif "workflow" in name:
            kind = NodeKind.WORKFLOW
        elif "handoff" in name or "router" in name or "goto" in name:
            kind = NodeKind.ROUTER
    if kind == NodeKind.DETERMINISTIC_TOOL and (
        _attr_get(attrs, "gen_ai.tool.type") == "datastore" or "search" in str(tool or "")
    ):
        kind = NodeKind.RETRIEVER
    ns = _attr_get(attrs, "langgraph_checkpoint_ns")
    if ns and kind in {NodeKind.SUBAGENT, NodeKind.UNKNOWN} and op in {
        "invoke_agent",
        "create_agent",
        "invoke_workflow",
    }:
        kind = NodeKind.SUBAGENT if op != "invoke_workflow" else NodeKind.WORKFLOW
    tool_name = str(tool or "")
    if kind == NodeKind.DETERMINISTIC_TOOL and (
        tool_name.startswith("transfer_to_") or "handoff" in tool_name.lower()
    ):
        kind = NodeKind.ROUTER
    det = {
        NodeKind.DETERMINISTIC_TOOL: DetClass.DETERMINISTIC,
        NodeKind.RETRIEVER: DetClass.STOCHASTIC_INDEX,
        NodeKind.LLM_REASONER: DetClass.LLM,
        NodeKind.SUBAGENT: DetClass.COMPOSITE,
        NodeKind.ROUTER: DetClass.DETERMINISTIC,
        NodeKind.WORKFLOW: DetClass.COMPOSITE,
        NodeKind.UNKNOWN: DetClass.COMPOSITE,
    }[kind]
    temp = _attr_get(attrs, "gen_ai.request.temperature")
    seed = _attr_get(attrs, "gen_ai.request.seed")
    if kind == NodeKind.LLM_REASONER and seed is not None and str(temp) in {"0", "0.0"}:
        det = DetClass.LLM_SEEDED
    return node_id, kind, det
