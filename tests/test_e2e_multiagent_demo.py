"""E2E: layered delivery-orchestrator harness nests agents for Studio."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "e2e-multiagent"
HARNESS = DEMO / "harness.py"


@pytest.mark.skipif(not HARNESS.is_file(), reason="multiagent demo harness missing")
def test_harness_nests_agents_and_surfaces(tmp_path: Path) -> None:
    pytest.importorskip("langgraph")
    pytest.importorskip("langchain_core")

    traces = tmp_path / "traces.json"
    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--n", "4", "--out", str(traces)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(traces.read_text(encoding="utf-8"))
    assert len(payload["traces"]) == 4
    assert payload.get("advisor.model") == "agent-as-model"

    studio = subprocess.run(
        [
            sys.executable,
            "-m",
            "superdeterminism",
            "studio-report",
            str(traces),
            "--n-min",
            "1",
            "--out",
            str(tmp_path / "studio.json"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert studio.returncode == 0, studio.stderr
    report = json.loads((tmp_path / "studio.json").read_text(encoding="utf-8"))
    root_ids = {n["node_id"] for n in report["graph"]["nodes"]}
    assert "supervisor" in root_ids
    assert "research_agent" in root_ids or "implement_agent" in root_ids
    assert "web_search" not in root_ids
    agents = [n for n in report["graph"]["nodes"] if n.get("subgraph")]
    assert agents, "expected nested specialist subgraphs"
    surfaces = {
        c.get("surface")
        for n in agents
        for c in n["subgraph"]["nodes"]
        if c.get("surface")
    }
    assert surfaces & {"mcp", "skill", "tool"}
    assert report["simulation_events"][0]["node_id"] == "delivery_orchestrator"
