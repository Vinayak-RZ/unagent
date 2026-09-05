from __future__ import annotations

import json
from pathlib import Path

import pytest

from superdeterminism.mcp_server import (
    ToolError,
    call_tool,
    list_tools,
    unagent_inspect,
    unagent_recommend,
    unagent_scaffold,
    unagent_simulate,
    unagent_validate,
)

EX = Path(__file__).resolve().parents[2] / "examples" / "advisor_flip_to_det.json"


def test_list_tools_exports_all_unagent_tools() -> None:
    names = {t["name"] for t in list_tools()}
    assert names == {
        "unagent_validate",
        "unagent_inspect",
        "unagent_recommend",
        "unagent_simulate",
        "unagent_scaffold",
    }


def test_unagent_validate_example() -> None:
    out = unagent_validate({"path": str(EX)})
    assert out == {"ok": True, "traces": 40, "spans": 40}


def test_unagent_validate_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    with pytest.raises(ToolError, match="does not exist"):
        unagent_validate({"path": str(missing)})


def test_unagent_inspect_example() -> None:
    out = unagent_inspect({"path": str(EX)})
    assert "nodes" in out
    assert any(n.get("node_id") == "classify" for n in out["nodes"])


def test_unagent_recommend_example() -> None:
    out = unagent_recommend({"path": str(EX), "n_min": 1})
    assert out["disclaimer"].startswith("simulation")
    rec = out["recommendations"][0]
    assert rec["node_id"] == "classify"
    assert rec["action"] == "FlipToDet"


def test_unagent_simulate_what_if() -> None:
    out = unagent_simulate(
        {"path": str(EX), "mode": "what-if", "node": "classify", "n_min": 1}
    )
    assert out["action"] == "FlipToDet"
    assert out["node_id"] == "classify"


def test_unagent_simulate_report() -> None:
    out = unagent_simulate({"path": str(EX), "mode": "report", "n_min": 1})
    assert "recommendations" in out
    assert "simulation" in out


def test_unagent_scaffold_writes_under_out_dir(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "disclaimer": "simulation != production; canary is confirmatory",
                "recommendations": [
                    {
                        "node_id": "classify",
                        "action": "FlipToDet",
                        "reasons": ["schema_ok high"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "scaffold" / "RUN"
    result = unagent_scaffold({"report_path": str(report_path), "out_dir": str(out_dir)})
    assert "REPORT.md" in result["files"]
    assert (out_dir / "REPORT.md").is_file()
    assert all(Path(out_dir, f).is_file() for f in result["files"])


def test_call_tool_dispatch() -> None:
    out = call_tool("unagent_validate", {"path": str(EX)})
    assert out["ok"] is True


def test_call_tool_unknown() -> None:
    with pytest.raises(ToolError, match="unknown tool"):
        call_tool("no_such_tool", {})
