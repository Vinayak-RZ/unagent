# E2E demo — Delivery orchestrator → Unagent Studio

Layered subject: supervisor + research / implement / review agents + policy gate.
Model: **agent-as-model** (this repo’s lead agent authored the cassettes). See [SUBJECT.md](SUBJECT.md).

## Regenerate

```bash
pip install -e ".[dev,langgraph]"
./demos/e2e-multiagent/run_pipeline.sh
```

## Open Studio

```bash
cd ui && npm install && npm run dev
# http://127.0.0.1:5173/?report=/e2e_multiagent_studio_report.json
```

Click an agent to open its tools / MCP / skills. Press Play: the canvas starts on the orchestration layer, then follows the task into the assigned agent.

Simulation ≠ production. Scaffold under `scaffold/` is illustrative only — never auto-applied.
