# Phase P3 completion — Multi-layer orchestration demo

**Branch:** `cursor/multi-layer-orchestration-demo-0e05`  
**Date:** 2026-09-06

## Completed

- `demos/e2e-orchestrator/` harness, 40 traces, pipeline, agent-as-model traces
- `graph_hierarchy.py` + `studio-report` nested subgraph + `narrative` + cinematic events
- Studio layer lens, cinematic playback, orchestrator demo URL
- E2E report, layer PNGs, simulation MP4
- Tests: `test_graph_hierarchy`, `test_e2e_orchestrator_demo`; `validate.sh` orchestrator smoke

## Validation

```text
PYTHONPATH=src python3 -m pytest -q  → 78 passed, 1 skipped
./scripts/validate.sh                 → OK
cd ui && npm test && npm run build    → OK
```

## P0 exit criteria

| Criterion | Status |
|-----------|--------|
| ≥40 traces, ≥3 advisor actions | pass (`supervisor_gate` FlipToDet + ABSTAINs) |
| Nested `subgraph` on orchestrator | pass (`task_router` → 3 agents → L2 tools) |
| Layer lens L0/L1/L2 | pass |
| Cinematic playback phases | pass |
| E2E report + PNGs + MP4 | pass |
| `narrative` improvement bullets | pass |
| Agent-as-model traces | pass (`traces_agent_model.json`) |
| `validate.sh` green | pass |

## P1 deferred

- Per-run comparison heatmap in Studio
- Headless `capture_studio_layers.sh` (Playwright)
- Live OTLP from cloud agent session

## What you learned

- Hierarchy is a **presentation layer** on flat `reconstruct()` — recommend pipeline unchanged; `advisor.layer` tags are the contract.
- FlipToDet needs **identical outputs** across pooled runs; varying routes belong on a separate node (`task_router`) while `supervisor_gate` stays stable.
- Studio breadcrumb UI was already built; wiring backend `subgraph` emission unlocked the multi-layer story without React Flow changes.
