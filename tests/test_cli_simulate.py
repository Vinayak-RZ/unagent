from __future__ import annotations

from pathlib import Path

from superdeterminism.cli import main

EX = Path(__file__).resolve().parents[1] / "examples" / "advisor_flip_to_det.json"


def test_cli_simulate_what_if(capsys) -> None:
    code = main(["simulate", str(EX), "--mode", "what-if", "--node", "classify"])
    assert code == 0
    out = capsys.readouterr().out
    assert "FlipToDet" in out
