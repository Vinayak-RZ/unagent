# Contributing to Unagent

Package name: `superdeterminism`. Product: Unagent. Repo: [Vinayak-RZ/unagent](https://github.com/Vinayak-RZ/unagent).

P0/P1 plus fail-closed L0 hardening are in `src/superdeterminism/`. Useful contributions: planted fixtures, producer mappings, docs that keep claim hygiene, adapter examples. Do not auto-apply refactors.

## Cursor config

Rules and skills come from the vendored [cursor-config-coding](https://github.com/Vinayak-RZ/cursor-config-coding) tree under `.cursor/`. Read [AGENTS.md](AGENTS.md) first.

## Before you write

1. Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), and [AGENTS.md](AGENTS.md).
2. Read [docs/overview.md](docs/overview.md) and [docs/landscape.md](docs/landscape.md).
3. Differentiation: counterfactual *re-typing* on ingested production graphs — not scoring the path you already ran, not searching a new workflow, not generic trace-driven determinization.

## Docs

- Keep research docs under ~400 lines. Citations in [docs/references.md](docs/references.md).
- OpenTelemetry GenAI is **Development**; pin a commit.
- Never invent `gen_ai.*` keys.

## Code

- Core: no LangChain / LangGraph / CrewAI imports except `adapters/langgraph.py`.
- `python -m pytest -q` and `scripts/validate.ps1` must pass.
- CLI stays non-interactive.
- FlipToDet requires cassette-tier L0 evidence. Unknown/mixed/failing nodes ABSTAIN.

## License

Apache License 2.0. See [LICENSE](LICENSE).
