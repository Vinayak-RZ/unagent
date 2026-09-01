from __future__ import annotations

from superdeterminism.models import ReplayStatus, Span, Trace
from superdeterminism.replay import splice_node, tape_from_traces, verify_tape


def test_tape_tamper_detected() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "c"},
                    input={"q": 1},
                    output={"a": 1},
                )
            ]
        )
    ]
    tape = tape_from_traces(traces)
    assert verify_tape(tape)
    rec = next(iter(tape["records"].values()))
    rec["output"] = "mutated"
    assert verify_tape(tape) is False


def test_splice_stable_without_children() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "c"},
                    input={"q": 1},
                    output={"a": 1},
                )
            ]
        )
        for _ in range(5)
    ]
    tape = tape_from_traces(traces)
    status = splice_node(traces, "c", tape, {"a": 1})
    assert status is ReplayStatus.TAIL_STABLE


def test_splice_diverges_on_new_output() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "c"},
                    input={"q": i},
                    output={"a": i},
                )
            ]
        )
        for i in range(3)
    ]
    tape = tape_from_traces(traces)
    status = splice_node(traces, "c", tape, {"a": 0})
    assert status is ReplayStatus.DIVERGED


def test_splice_refuses_mutating_miss() -> None:
    recorded = [
        Trace(
            spans=[
                Span(
                    name="execute_tool issue_refund",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "issue_refund",
                    },
                    input={"id": 1},
                    output={"ok": True},
                )
            ]
        )
    ]
    tape = tape_from_traces(recorded)
    unseen = [
        Trace(
            spans=[
                Span(
                    name="execute_tool issue_refund",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "issue_refund",
                    },
                    input={"id": 99},
                    output={"ok": True},
                )
            ]
        )
    ]
    status = splice_node(unseen, "issue_refund", tape, {"ok": True})
    assert status is ReplayStatus.REFUSED_MUTATING
