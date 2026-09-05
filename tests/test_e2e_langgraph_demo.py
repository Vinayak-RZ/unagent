"""E2E harness: LangGraph research-assistant mirror produces FlipToDet on guard_input."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demos" / "e2e-langgraph"
HARNESS = DEMO / "harness.py"


@pytest.mark.skipif(
    not HARNESS.is_file(),
    reason="e2e demo harness missing",
)
def test_harness_and_recommend_flip_guard(tmp_path: Path) -> None:
    pytest.importorskip("langgraph")
    pytest.importorskip("langchain_core")

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
        [
            sys.executable,
            "-m",
            "superdeterminism",
            "recommend",
            str(traces),
            "--adapter",
            "langgraph",
            "--stdout",
            "json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rec.returncode == 0, rec.stderr
    report = json.loads(rec.stdout)
    by_id = {r["node_id"]: r["action"] for r in report["recommendations"]}
    assert by_id.get("guard_input") == "FlipToDet"
    assert by_id.get("model") == "ABSTAIN"
