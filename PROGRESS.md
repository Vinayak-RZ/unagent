# Progress — Unagent

## P3 — Multi-layer orchestration demo (2026-09-06)

Branch: `cursor/multi-layer-orchestration-demo-0e05`  
Plan: [docs/plans/P3-multi-layer-orchestration-demo.md](docs/plans/P3-multi-layer-orchestration-demo.md)  
Completion: [PHASE_P3_COMPLETION.md](PHASE_P3_COMPLETION.md)

| Phase | Status | Notes |
|-------|--------|-------|
| 0 ADR | done | [0014-hierarchical-studio-graph.md](docs/decisions/0014-hierarchical-studio-graph.md) |
| A Harness + traces | done | `demos/e2e-orchestrator/`, n=40 |
| B Hierarchy core | done | `graph_hierarchy.py`, narrative, cinematic events |
| C Studio UX | done | Layer lens, cinematic playback |
| D/E Report + media | done | [E2E_ORCHESTRATOR_STUDIO.md](docs/reports/E2E_ORCHESTRATOR_STUDIO.md) |
| N Validation | done | `validate.sh`, e2e test, UI tests |

---

## Viral product hardening (prior)

Branch: `cursor/unagent-viral-hardening-c4f0`

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Design + ADRs | done | DESIGN-meta, PRODUCT, DESIGN, ADRs |
| S Simulate API | done | `simulate` CLI + L0 events + tests |
| I Sinks | done | Langfuse/LangSmith/MLflow file+live |
| A MCP + Python API | done | `unagent-mcp` stdio server |
| R Narrative + README | done | `--stdout narrative` + viral quickstart |
| U Studio UI | done | React Flow viewer + playback + proposal export |
| B Track B adapter | done | CrewAI + refuse-with-reason |
| H Hardening | done | CI extras+UI, `scripts/validate.sh`, security notes, PyPI checklist |

Authority: viral product hardening master plan (nawab). Do not edit the plan file in artifacts.

## Cutover

- PyPI publish remains **human-gated** — see `docs/pypi-checklist.md`
- Studio walkthrough media: `docs/assets/e2e-orchestrator/` (orchestrator demo)
