# Unagent — extensive internals

Companion to the main [README](../README.md). How the repo runs, first-party modules, and why files exist.

## 1. How this repository runs

CLI against a JSON trace file. Validate/inspect optional. Recommend reconstructs a graph, builds a hash-verified L0 cassette, and fail-closes to ABSTAIN unless a cassette-stable flip is certified. Scaffold writes under `--out` only.

```text
traces.json → ingest → classify → graph → evidence → L0 splice → recommend → JSON/MD
report.json → scaffold → REPORT.md WIRING.md generated/ patches/
```

## 2. Package map

| Package | Path | Role |
|---------|------|------|
| `superdeterminism` | `src/superdeterminism/` | Core advisor |
| tests | `tests/` | pytest |
| examples | `examples/` | ABSTAIN + FlipToDet demos |
| schemas | `schemas/report-v1.json` | Report contract |
| benchmarks | `benchmarks/planted/` | Planted DET traces, not product accuracy |

## 3. Modules

| File | Why |
|------|-----|
| `models.py` | Public types + schema versions |
| `ingest.py` | Untrusted-file limits, OTLP status/IDs |
| `classify.py` | span → node_kind / det.class |
| `graph.py` | V,E, completeness, trust, commitment |
| `evidence.py` | Trace sampling unit, Wilson, tiers |
| `replay.py` | Cassette hash, splice, mutating refuse |
| `pipeline.py` | Fail-closed `_decide` + report dict |
| `cli.py` | recommend, validate, inspect, scaffold |
| `scaffold.py` | Atomic write-only artifacts |
| `adapters/` | langgraph, custom, atif |

## 4. Tests and CI

```bash
pip install -e ".[dev]"
python -m pytest -q
```

CI: `.github/workflows/ci.yml` (Python 3.10–3.14). Orchestrator: `scripts/validate.ps1`.

## 5. Ideas

Evidence tiers: observational cannot certify a flip. L0 cassette can. L1/L2 stay opt-in / external. Differentiation is determinism-class re-typing, not Progressive Crystallization-style auto promotion and not FlowScout search.
