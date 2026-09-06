"""Agent-as-model trace capture — scripted cloud-agent scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness import OUT_DEFAULT, run_once, _load_scenarios

# ponytail: reuses harness emitter; cloud agent runs these scenarios in validation


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "traces_agent_model.json")
    p.add_argument("--scenarios", type=Path, default=Path(__file__).resolve().parent / "scenarios.json")
    args = p.parse_args(argv)

    scenarios = _load_scenarios(args.scenarios)
    # One trace per scenario — agent-as-model walkthrough
    traces = [run_once(sc, i) for i, sc in enumerate(scenarios)]
    payload = {"traces": traces, "source": "agent-as-model-scripted"}
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(traces)} traces)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
