# E2E demo — Multi-layer orchestrator → Unagent Studio

Three-layer topology:

```text
L0 task_router (supervisor)
  ├─ research_agent → web_search | mcp_arxiv | skill_docs
  ├─ code_agent     → code_exec | skill_lint
  └─ data_agent     → sql_query | mcp_warehouse
```

## Regenerate

```bash
pip install -e ".[dev]"
python demos/e2e-orchestrator/harness.py --n 40 --out demos/e2e-orchestrator/traces.json
./demos/e2e-orchestrator/run_pipeline.sh
```

## Open Studio

```bash
cd ui && npm install && npm run dev
# http://127.0.0.1:5173/?report=/e2e_orchestrator_studio_report.json
```

Or: `python -m superdeterminism ui --report demos/e2e-orchestrator/studio_report.json --no-open`

## Expected advisor highlights (n=40)

| Node | Typical action | Notes |
|------|----------------|-------|
| `task_router` | **FlipToDet** | Stable routing JSON across runs |
| `research_agent` | ABSTAIN | Tool-then-answer vs direct-answer divergence |
| `code_agent` / `data_agent` | ABSTAIN or FlipToDet | Depends on scenario mix |
| L2 tools | ABSTAIN | Already deterministic |

Simulation ≠ production. See `docs/reports/E2E_ORCHESTRATOR_STUDIO.md`.
