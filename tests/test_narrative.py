"""Tests for architecture improvement narrative."""

from __future__ import annotations

from superdeterminism.narrative import build_narrative


def test_build_narrative_includes_flip_and_diverged() -> None:
    md = build_narrative(
        {
            "recommendations": [
                {
                    "node_id": "task_router",
                    "action": "FlipToDet",
                    "n": 40,
                    "p_mode_lower": 0.91,
                    "replay_status": "tail_stable",
                },
                {
                    "node_id": "research_agent",
                    "action": "ABSTAIN",
                    "replay_status": "diverged",
                },
            ]
        }
    )
    assert "task_router" in md
    assert "FlipToDet" in md or "deterministic" in md
    assert "research_agent" in md
    assert "diverged" in md
