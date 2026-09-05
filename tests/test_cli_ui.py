from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main

EX = Path(__file__).resolve().parents[1] / "examples" / "advisor_flip_to_det.json"


def test_cli_studio_report(tmp_path: Path) -> None:
    out = tmp_path / "studio.json"
    code = main(["studio-report", str(EX), "--out", str(out), "--n-min", "1"])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["recommendations"]
    assert payload["simulation_events"]
    assert payload["graph"]["nodes"]


def test_cli_ui_prints_instructions(capsys) -> None:
    code = main(["ui", "--no-open"])
    assert code == 0
    err = capsys.readouterr().err
    assert "Unagent Studio" in err
    assert "never auto-applied" in err
