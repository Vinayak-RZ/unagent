# E2E demo — LangGraph research assistant → Unagent Studio

Subject: [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) `research_assistant` topology (guard → model ⇄ tools).

## Regenerate

```bash
pip install -e ".[dev,langgraph]"
python demos/e2e-langgraph/harness.py --n 40 --out demos/e2e-langgraph/traces.json
./demos/e2e-langgraph/run_pipeline.sh
```

## Open Studio

```bash
cp demos/e2e-langgraph/studio_report.json ui/public/e2e_studio_report.json
cd ui && npm install && npm run dev
# open http://127.0.0.1:5173/?report=/e2e_studio_report.json
```

Or: `python -m superdeterminism ui --report demos/e2e-langgraph/studio_report.json --no-open`

## Expected advisor result (cassette L0)

| Node | Action | Notes |
|------|--------|-------|
| `guard_input` | **FlipToDet** | Stable safety JSON across n=40; Wilson lower ≥ 0.91 |
| `model` | ABSTAIN | Tool-call then answer → cassette diverged |
| `calculator` | ABSTAIN | Already deterministic |

Simulation ≠ production. Scaffold under `scaffold/` is illustrative only — never auto-applied.
