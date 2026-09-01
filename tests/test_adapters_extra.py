from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main
from superdeterminism.adapters.atif import load as load_atif
from superdeterminism.adapters.custom import load as load_custom


def test_atif_maps_tool_and_chat() -> None:
    traces = load_atif(
        json.dumps(
            {
                "trajectory_id": "t1",
                "steps": [
                    {"type": "assistant", "content": {"plan": "x"}},
                    {
                        "type": "tool_call",
                        "name": "lookup",
                        "arguments": {"id": 1},
                        "observation": {"ok": True},
                    },
                ],
            }
        ).encode()
    )
    assert len(traces[0].spans) == 2
    assert traces[0].spans[1].attributes["gen_ai.operation.name"] == "execute_tool"


def test_custom_events(tmp_path: Path) -> None:
    path = tmp_path / "e.json"
    path.write_text(
        json.dumps(
            {
                "events": [
                    {"name": "classify", "op": "chat", "output": {"intent": "a"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    traces = load_custom(path)
    assert traces[0].spans[0].name == "classify"


def test_cli_adapter_custom(tmp_path: Path, capsys) -> None:
    path = tmp_path / "e.json"
    path.write_text(
        json.dumps(
            {
                "traces": [
                    {
                        "spans": [
                            {
                                "name": "chat",
                                "attributes": {"gen_ai.operation.name": "chat"},
                                "output": {"a": 1},
                            }
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["recommend", str(path), "--adapter", "custom", "--n-min", "1"]) == 0
    assert json.loads(capsys.readouterr().out)["recommendations"]
