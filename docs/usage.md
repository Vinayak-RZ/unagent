# Usage

Agents and humans use the same CLI. No prompts. No auto-apply. Core has **no** LangChain import.

```bash
pip install -e ".[dev]"
python -m superdeterminism recommend examples/advisor_stable_llm.json --n-min 1 --stdout json
python -m superdeterminism recommend examples/advisor_flip_to_det.json --stdout json
python -m superdeterminism validate examples/advisor_stable_llm.json
python -m superdeterminism inspect examples/advisor_stable_llm.json
python -m superdeterminism recommend traces.json --json out.json --md out.md --n-min 30
python -m superdeterminism recommend --traces-dir DIR --stdout json
```

Exit `0` if a report was produced (including all-ABSTAIN). Exit `2` on bad input, unknown adapter, or missing extra.

Report schema: [schemas/report-v1.json](../schemas/report-v1.json). Troubleshooting: [troubleshooting.md](troubleshooting.md).

## LangGraph adapter

```bash
pip install -e ".[dev,langgraph]"
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

`--adapter custom` and `--adapter atif` need no extra. `--adapter langgraph` without the extra exits `2`.

`scaffold` writes `REPORT.md`, `WIRING.md`, `ADAPTERS.md`, `CANARY.md`, `generated/`, and `patches/*.diff` under `--out`. It does **not** edit `graph.py`. Stale patches in `--out` are removed.

## Output (JSON)

Top-level: `report_version`, `advisor.schema_version`, `estimator` (`observational_l0_proxy` or `l0_tape_splice`), `evidence_ceiling`, `graph_identity`, `graph_completeness`, `graph_trust`, `tape_version`, `input_hash`, `recommendations[]`, `canary[]`.

Each row includes `evidence_tier`, `replay_status`, `deltas`, `mixed`. Actions: `FlipToDet` | `FlipToNondet` | `STRENGTHEN_SDB` | `ABSTAIN`.

FlipToDet requires cassette-stable L0 splice, schema/p_mode/Wilson, failure_rate = 0, and a metric improvement. Unknown/mixed nodes ABSTAIN.

Default `--n-min 30`. Task success: `advisor.outcome.success` or `--outcome-attr`. Otherwise `task_success` is null (`not_supplied`).
