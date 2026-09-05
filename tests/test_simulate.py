from __future__ import annotations

from pathlib import Path

from superdeterminism.ingest import load_traces_path
from superdeterminism.simulate import simulate_design, simulate_report, simulate_what_if

EX = Path(__file__).resolve().parents[1] / "examples" / "advisor_flip_to_det.json"


def test_what_if_flip_to_det() -> None:
    traces = load_traces_path(EX)
    result = simulate_what_if(traces, "classify", n_min=30)
    assert result.action == "FlipToDet"
    assert result.replay_status == "tail_stable"
    assert any(e.kind == "splice" for e in result.events)


def test_design_ranks_classify() -> None:
    traces = load_traces_path(EX)
    design = simulate_design(traces, n_min=30)
    assert design
    assert design[0].node_id == "classify"


def test_report_includes_events() -> None:
    traces = load_traces_path(EX)
    report = simulate_report(traces, n_min=30)
    assert "simulation" in report
    assert "simulation_events" in report
    assert report["simulation"]["l1_executed"] is False


def test_missing_node_abstains() -> None:
    traces = load_traces_path(EX)
    result = simulate_what_if(traces, "nope", n_min=1)
    assert result.action == "ABSTAIN"
