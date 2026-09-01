from __future__ import annotations

import json
from pathlib import Path

from superdeterminism.cli import main


def test_scaffold_clears_stale_patches(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "patches").mkdir()
    (out / "patches" / "old.diff").write_text("stale", encoding="utf-8")
    report = tmp_path / "r.json"
    report.write_text(
        json.dumps(
            {
                "estimator": "observational_l0_proxy",
                "recommendations": [
                    {"node_id": "classify", "action": "ABSTAIN", "reasons": ["n"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["scaffold", str(report), "--out", str(out)]) == 0
    assert not (out / "patches" / "old.diff").exists()


def test_scaffold_bad_report_exits_2(tmp_path: Path) -> None:
    report = tmp_path / "r.json"
    report.write_text("[]", encoding="utf-8")
    assert main(["scaffold", str(report), "--out", str(tmp_path / "o")]) == 2


def test_malformed_recommend_exits_2(tmp_path: Path) -> None:
    path = tmp_path / "t.json"
    path.write_text(json.dumps({"traces": [1]}), encoding="utf-8")
    assert main(["recommend", str(path)]) == 2
