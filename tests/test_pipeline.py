from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.models import Action, DetClass, NodeKind, Span, Trace
from superdeterminism.pipeline import (
    classify_span,
    load_traces,
    recommend_traces,
    wilson_lower,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _repeat_trace(template: dict, n: int, *, mutate=None) -> dict:
    traces = []
    for i in range(n):
        raw = json.loads(json.dumps(template["traces"][0]))
        if mutate:
            mutate(raw, i)
        traces.append(raw)
    return {"traces": traces}


def test_classify_chat_and_tool() -> None:
    chat = Span(
        name="chat gpt-4",
        attributes={"gen_ai.operation.name": "chat"},
    )
    tool = Span(
        name="execute_tool lookup_order",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "lookup_order",
        },
    )
    node, kind, det = classify_span(chat)
    assert kind is NodeKind.LLM_REASONER
    assert det is DetClass.LLM
    node, kind, det = classify_span(tool)
    assert node == "lookup_order"
    assert kind is NodeKind.DETERMINISTIC_TOOL


def test_load_otlp() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "name": "chat gpt-4",
                                "attributes": [
                                    {
                                        "key": "gen_ai.operation.name",
                                        "value": {"stringValue": "chat"},
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }
    traces = load_traces(payload)
    assert len(traces) == 1
    assert traces[0].spans[0].attributes["gen_ai.operation.name"] == "chat"


def test_flip_to_det_when_stable_schema() -> None:
    template = json.loads((FIXTURES / "advisor_stable_llm.json").read_text())
    traces = load_traces(_repeat_trace(template, 40))
    recs = recommend_traces(traces, n_min=30)
    classify = next(r for r in recs if r.node_id == "classify")
    assert classify.action is Action.FLIP_TO_DET
    assert classify.schema_ok >= 0.8
    assert classify.p_mode >= 0.7
    assert classify.evidence_tier == "cassette"
    assert classify.replay_status == "tail_stable"
    assert classify.deltas


def test_abstain_when_n_below_min() -> None:
    template = json.loads((FIXTURES / "advisor_stable_llm.json").read_text())
    traces = load_traces(_repeat_trace(template, 5))
    recs = recommend_traces(traces, n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert "n_min" in recs[0].reasons[0]


def test_strengthen_sdb_on_sensitive_llm() -> None:
    span = Span(
        name="chat",
        attributes={
            "gen_ai.operation.name": "chat",
            "langgraph_node": "issue_refund",
        },
        output={"ok": True},
    )
    recs = recommend_traces([Trace(spans=[span] * 40)], n_min=30)
    assert recs[0].action is Action.STRENGTHEN_SDB


def test_flip_to_nondet_on_failing_tool() -> None:
    span = Span(
        name="execute_tool parse_fields",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "parse_fields",
        },
        output="nope",
        error=True,
    )
    recs = recommend_traces([Trace(spans=[span]) for _ in range(40)], n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert "FlipToNondet" in recs[0].reasons[0]


def test_unknown_ops_abstain() -> None:
    span = Span(name="mystery", attributes={"gen_ai.operation.name": "not_a_real_op"})
    recs = recommend_traces([Trace(spans=[span]) for _ in range(40)], n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert recs[0].node_kind is NodeKind.UNKNOWN


def test_failed_llm_does_not_flip() -> None:
    span = Span(
        name="chat",
        attributes={"gen_ai.operation.name": "chat", "langgraph_node": "classify"},
        output={"intent": "x"},
        error=True,
    )
    recs = recommend_traces([Trace(spans=[span]) for _ in range(40)], n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert recs[0].failure_rate == 1.0


def test_mixed_kinds_abstain_order_invariant() -> None:
    chat = Span(
        name="chat",
        attributes={"gen_ai.operation.name": "chat", "langgraph_node": "n"},
        output={"a": 1},
    )
    tool = Span(
        name="execute_tool n",
        attributes={"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": "n"},
        output={"a": 1},
    )
    a = recommend_traces(
        [Trace(spans=[chat]), Trace(spans=[tool])] * 20, n_min=30
    )
    b = recommend_traces(
        [Trace(spans=[tool]), Trace(spans=[chat])] * 20, n_min=30
    )
    assert a[0].action is Action.ABSTAIN
    assert b[0].action is Action.ABSTAIN
    assert a[0].mixed and b[0].mixed


def test_error_false_string_is_not_failure() -> None:
    from superdeterminism.ingest import load_traces

    traces = load_traces(
        {
            "traces": [
                {
                    "spans": [
                        {
                            "name": "chat",
                            "attributes": {"gen_ai.operation.name": "chat"},
                            "error": "false",
                            "output": {"ok": True},
                        }
                    ]
                }
            ]
        }
    )
    assert traces[0].spans[0].error is False


def test_wilson_lower_is_below_phat() -> None:
    assert 0 < wilson_lower(21, 30) < 21 / 30


def test_mixed_workload_abstains_flip() -> None:
    traces = []
    for i in range(40):
        model = "gpt-4.1-mini" if i < 20 else "gpt-4.1"
        traces.append(
            Trace(
                spans=[
                    Span(
                        name="chat",
                        attributes={
                            "gen_ai.operation.name": "chat",
                            "langgraph_node": "classify",
                            "gen_ai.request.model": model,
                        },
                        input={"q": 1},
                        output={"intent": "x"},
                    )
                ]
            )
        )
    recs = recommend_traces(traces, n_min=30)
    assert recs[0].action is Action.ABSTAIN
    assert "workload" in recs[0].reasons[0]


def test_interaction_hypotheses_on_adjacent_failures() -> None:
    traces = [
        Trace(
            spans=[
                Span(
                    name="execute_tool a",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "parse_a",
                    },
                    span_id="a",
                    output="nope",
                    error=True,
                ),
                Span(
                    name="execute_tool b",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "parse_b",
                    },
                    span_id="b",
                    parent_span_id="a",
                    output="nope",
                    error=True,
                ),
            ]
        )
        for _ in range(40)
    ]
    recs = recommend_traces(traces, n_min=30)
    assert any(r.interaction_hypotheses for r in recs)
