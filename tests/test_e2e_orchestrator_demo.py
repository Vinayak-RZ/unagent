"""E2E harness: multi-layer orchestrator produces FlipToDet on task_router."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "e2e-orchestrator"
HARNESS = DEMO / "harness.py"


@pytest.mark.skipif(not HARNESS.is_file(), reason="e2e orchestrator harness missing")
def test_harness_and_hierarchical_studio_report(tmp_path: Path) -> None:
    traces = tmp_path / "traces.json"
    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--n", "40", "--out", str(traces)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(traces.read_text(encoding="utf-8"))
    assert len(payload["traces"]) == 40

    rec = subprocess.run(
        [sys.executable, "-m", "superdeterminism", "recommend", str(traces), "--stdout", "json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rec.returncode == 0, rec.stderr
    report = json.loads(rec.stdout)
    by_id = {r["node_id"]: r["action"] for r in report["recommendations"]}
    assert by_id.get("supervisor_gate") == "FlipToDet"
    assert by_id.get("research_agent") == "ABSTAIN"

    studio = tmp_path / "studio.json"
    sr = subprocess.run(
        [
            sys.executable,
            "-m",
            "superdeterminism",
            "studio-report",
            str(traces),
            "--out",
            str(studio),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert sr.returncode == 0, sr.stderr
    studio_report = json.loads(studio.read_text(encoding="utf-8"))
    assert studio_report.get("narrative")
    root = studio_report["graph"]["nodes"][0]
    assert root.get("subgraph")
    events = studio_report.get("simulation_events") or []
    kinds = {e.get("kind") for e in events}
    assert "layer_enter" in kinds
    assert "assign_task" in kinds
