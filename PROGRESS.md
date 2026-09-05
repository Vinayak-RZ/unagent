# Progress — viral product hardening

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
- Production GIFs/videos remain user-owned
