# Changelog

## Unreleased — viral product hardening

- First-class `simulate` (what-if / design / report) with L0 cassette events; L1 opt-in gated
- Sinks: Langfuse, LangSmith, MLflow (file export + live env-gated)
- MCP server (`unagent-mcp`) + Python API parity with CLI
- Narrative stdout for non-technical readers
- Unagent Studio (`ui/`): React Flow viewer, sim playback, in-graph **proposal draft** export only
- CrewAI adapter with refuse-with-reason for LangGraph-shaped payloads
- CI: extras matrix + UI job; `scripts/validate.sh`; security review notes; PyPI checklist (publish human-gated)

## 0.1.0

- Agnostic CLI `recommend` / `validate` / `inspect` / `scaffold`
- Fail-closed recommendations (unknown, mixed, failing, observational-only)
- OTLP ingest with status/IDs, graph reconstruction, L0 hash-verified cassette
- Adapters: langgraph (extra), custom, atif
- Report schema v1 (`schemas/report-v1.json`) and tape schema (`schemas/tape-v1.json`)
