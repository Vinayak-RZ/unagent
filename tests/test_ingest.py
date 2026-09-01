from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main
from superdeterminism.ingest import IngestError, load_traces, load_traces_path
from superdeterminism.models import NodeKind
from superdeterminism.pipeline import classify_span, inspect_traces
import pytest


def test_otlp_status_error_code() -> None:
    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "name": "chat gpt-4",
                                "traceId": "aa",
                                "spanId": "s1",
                                "parentSpanId": "",
                                "status": {"code": 2},
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
    assert traces[0].spans[0].error is True
    assert traces[0].spans[0].span_id == "s1"


def test_finish_reason_error_alias() -> None:
    traces = load_traces(
        {
            "traces": [
                {
                    "spans": [
                        {
                            "name": "chat",
                            "attributes": {
                                "gen_ai.operation.name": "chat",
                                "gen_ai.response.finish_reason": "error",
                            },
                        }
                    ]
                }
            ]
        }
    )
    assert traces[0].spans[0].error is True


def test_malformed_traces_list_raises() -> None:
    with pytest.raises(IngestError):
        load_traces({"traces": [1]})


def test_tokens_object_does_not_crash() -> None:
    traces = load_traces(
        {
            "traces": [
                {
                    "spans": [
                        {
                            "name": "chat",
                            "attributes": {"gen_ai.operation.name": "chat"},
                            "tokens": {"prompt": 1},
                            "output": {"a": 1},
                        }
                    ]
                }
            ]
        }
    )
    assert traces[0].spans[0].tokens == 0


def test_file_too_large(tmp_path: Path) -> None:
    p = tmp_path / "big.json"
    p.write_bytes(b"{" + b"a" * 10)
    with pytest.raises(IngestError):
        load_traces_path(p, max_bytes=4)


def test_cli_validate_and_inspect(tmp_path: Path, capsys) -> None:
    path = tmp_path / "t.json"
    path.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "attributes": {
                                    "gen_ai.operation.name": "chat",
                                    "langgraph_node": "classify",
                                },
                                "output": {"intent": "x"},
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["validate", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert main(["inspect", str(path)]) == 0
    inspect = json.loads(capsys.readouterr().out)
    assert inspect["nodes"][0]["node_id"] == "classify"


def test_cli_traces_dir(tmp_path: Path, capsys) -> None:
    d = tmp_path / "batch"
    d.mkdir()
    for i in range(2):
        (d / f"{i}.json").write_text(
            json.dumps(
                {
                    "traces": [
                        {
                            "spans": [
                                {
                                    "name": "chat",
                                    "attributes": {"gen_ai.operation.name": "chat"},
                                    "output": {"k": i},
                                }
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
    assert main(["recommend", "--traces-dir", str(d), "--n-min", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_version"] == "1.0"


def test_router_from_handoff() -> None:
    from superdeterminism.models import Span
    from superdeterminism.pipeline import classify_span

    span = Span(
        name="execute_tool transfer_to_refund",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "transfer_to_refund",
        },
    )
    _, kind, _ = classify_span(span)
    assert kind is NodeKind.ROUTER


def test_inspect_traces_has_graph() -> None:
    from superdeterminism.models import Span, Trace

    traces = [
        Trace(
            spans=[
                Span(
                    name="chat",
                    attributes={"gen_ai.operation.name": "chat", "langgraph_node": "a"},
                    span_id="1",
                ),
                Span(
                    name="execute_tool t",
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": "t",
                    },
                    span_id="2",
                    parent_span_id="1",
                ),
            ],
            trace_id="t0",
        )
    ]
    info = inspect_traces(traces)
    assert info["edges"]
    assert info["completeness"] > 0
