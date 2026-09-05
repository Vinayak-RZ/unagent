# Security review — viral hardening (Phase H)

Date: 2026-09-05  
Scope: sinks (file + live), MCP stdio server, Studio UI proposal export, CLI.

## Findings

| ID | Severity | Area | Finding | Disposition |
|----|----------|------|---------|-------------|
| S1 | Medium | Live sinks | API keys read from env (`LANGFUSE_*`, `LANGSMITH_API_KEY`, `MLFLOW_*`). Live fetch writes ephemeral JSON under `/tmp`. | **Accept** with docs: never commit keys; prefer file exports in CI. |
| S2 | Low | MCP | Stdio tools wrap library calls; no shell execution; no filesystem write except caller-chosen paths. | **Accept** — document tool surface in README/MCP section. |
| S3 | Medium | Studio UI | Proposal edit is client-side only; export downloads JSON. No path that mutates agent source. | **Accept** — keep disclaimer banners; refuse auto-apply forever. |
| S4 | Low | CLI `ui --serve-dist` | Serves static `ui/dist` on localhost only. | **Accept** — do not bind `0.0.0.0` in this release. |
| S5 | Info | Report JSON | May contain span names / node ids from user traces. | **Accept** — privacy.md already warns traces are sensitive. |
| S6 | Low | Temp files | Live sinks use fixed `/tmp/unagent_*_live.json` names (possible clash on shared hosts). | **Follow-up** — use `tempfile.NamedTemporaryFile` in a later patch. |

## Explicit non-goals (still out of scope)

- Hosted multi-tenant SaaS
- Auto-apply / rewriting customer `graph.py`
- Inventing `gen_ai.*` attribute keys
- Storing credentials in repo or UI localStorage

## Residual risk

Simulation ≠ production. L0 cassette stability is necessary but not sufficient for FlipToDet promotion; canary remains confirmatory.
