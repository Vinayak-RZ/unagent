# Decisions

Index of significant choices. Formal ADRs land in `docs/decisions/` during Phase A.

| ID | Decision | Status | Record |
|---|---|---|---|
| D0 | Project name Superdeterminism; repo URL `superdeterminisiom` unchanged | superseded | this file; see D10 |
| D1 | Apache-2.0 license | accepted | [LICENSE](LICENSE) |
| D2 | Vendor cursor-config-coding into `.cursor/` (copy, not symlink) | accepted | [.cursor/VENDOR.md](.cursor/VENDOR.md) |
| D3 | Vendor guides live under `docs/cursor-config/` | accepted | this file |
| D4 | Ingest OTLP; Advisor fields in `advisor.*` / `det.*` | accepted | [0001-otel-ingest.md](docs/decisions/0001-otel-ingest.md) |
| D5 | v0 simulation is offline L0; no production-LLM re-run by default | accepted | [0002-v0-offline-first.md](docs/decisions/0002-v0-offline-first.md) |
| D6 | Report + optional scaffold; never auto-apply | accepted | [0003-no-auto-apply.md](docs/decisions/0003-no-auto-apply.md) |
| D7 | Product code requires a later project-mode nawab plan | superseded | P0 started; see D8 |
| D8 | Agnostic core; LangGraph and other stacks are adapters | accepted | [0004-agnostic-core.md](docs/decisions/0004-agnostic-core.md) |
| D9 | Re-vendor cursor-config-coding at 5ecaca9; product README + EXTENSIVE companion | accepted | this file |
| D10 | GitHub repo `unagent`; product Unagent; package `superdeterminism` | accepted | this file |
| D11 | Evidence tiers; observational cannot certify a flip | accepted | [0005-evidence-tiers.md](docs/decisions/0005-evidence-tiers.md) |
| D12 | `report_version` / `advisor.schema_version` 1.0 | accepted | [0006-schema-versioning.md](docs/decisions/0006-schema-versioning.md) |
| D13 | OTel GenAI pin + compatibility aliases | accepted | [0007-otel-pin.md](docs/decisions/0007-otel-pin.md) |
| D14 | Research-complete before public release | accepted | [0008-research-first-release.md](docs/decisions/0008-research-first-release.md) |
| D15 | User-supplied outcome contract | accepted | [0009-outcome-contract.md](docs/decisions/0009-outcome-contract.md) |

## D0 — Naming

- **Context:** GitHub repo is `superdeterminisiom`. Working title was Determinism Advisor.
- **Alternatives:** Rename the GitHub repo; drop Superdeterminism; use only Determinism Advisor.
- **Selected:** Keep the repo URL. Project name is Superdeterminism. Capability name is Determinism Advisor.
- **Rationale:** Avoids a rename mid-research. Names are documented in README and AGENTS.md.
- **Superseded by:** D10 (GitHub repo renamed to `unagent`; product name Unagent).

## D1 — License

- **Context:** Greenfield OSS methodology tool.
- **Alternatives:** MIT; unlicensed.
- **Selected:** Apache-2.0.
- **Rationale:** Patent grant; matches MLflow / DeepEval in the adjacent eval space.

## D2 — Cursor config vendor

- **Context:** Cloud Agents load `.cursor/skills` from the cloned app repo, not from a local junction.
- **Alternatives:** Git submodule + symlink; document-only pointer to cursor-config-coding.
- **Selected:** Copy `.cursor/` into this repo and pin the source commit.
- **Rationale:** cursor-config-coding’s own cloud-agent docs require committed files.

## D3 — Vendor doc location

- **Context:** Mixing SPEC_KIT / MCP guides with Superdeterminism research confused the doc map and created links to files that looked like product docs.
- **Alternatives:** Leave vendor guides in `docs/`; put them under `.cursor/docs/`.
- **Selected:** `docs/cursor-config/`.
- **Rationale:** Keeps research `docs/*.md` for the product contract only.

## D4–D6

Written as ADRs in `docs/decisions/`. Do not silently override them.

## D8 — Agnostic core

- **Context:** Need LangGraph *and* other agent stacks without locking the core.
- **Alternatives:** LangGraph-only package; if-import every framework.
- **Selected:** P0 core with zero framework deps; P1 LangGraph extra; P2 other stacks.
- **Rationale:** Adapters translate. Agents and humans call one CLI.

## D9 — README skills vendor + product landing

- **Context:** cursor-config-coding added `readme`, `product-readme`, `readable-readme`, and moved extensive output to `docs/EXTENSIVE.md`. This repo was pinned at 437a548.
- **Alternatives:** Cherry-pick only `product-readme`; keep a single exhaustive `README.md`; symlink to the config repo.
- **Selected:** Copy upstream at `5ecaca9c5a6e85be8ede01ef33e0af10651c622e`. Main `README.md` is a product landing. Internals live in `docs/EXTENSIVE.md`. Keep `docs/cursor-config/` remaps in `skills-manifest.json` (D3).
- **Rationale:** Cloud Agents load skills from this clone. The `readme` router forbids dumping internals into `README.md`.

## D10 — GitHub repo `unagent`

- **Context:** Product name is Unagent. GitHub was still `superdeterminisiom`. The remote was renamed to `unagent`.
- **Alternatives:** Keep the old slug; also rename the Python package to `unagent`.
- **Selected:** GitHub repo and clone URL are [`Vinayak-RZ/unagent`](https://github.com/Vinayak-RZ/unagent). Product name is Unagent. Installable package and `python -m` entry stay `superdeterminism`. Local checkout folder is `unagent`.
- **Rationale:** Matches the renamed GitHub repo without a PyPI/import break.

## D7 — No product code in this plan

- **Context:** Temptation to scaffold a Python package “for later.”
- **Alternatives:** Scaffold now; implement v0 in the same plan.
- **Selected:** Docs-only. Simulator needs a new approved project-mode plan.
- **Rationale:** nawab + ponytail: do not invent a package without an ADR and an approved plan.

| D16 | Simulate is a first-class product surface | accepted | [0010-simulate-as-core.md](docs/decisions/0010-simulate-as-core.md) |
| D17 | CLI preferred; Python + MCP wrap same library | accepted | [0011-mcp-cli-dual-surface.md](docs/decisions/0011-mcp-cli-dual-surface.md) |
| D18 | Sinks dual-mode file + live (Langfuse/LangSmith/MLflow) | accepted | [0012-sinks-dual-mode.md](docs/decisions/0012-sinks-dual-mode.md) |
| D19 | Studio UI: React Flow viewer + playback + proposal edit only | accepted | [0013-ui-studio-react-flow.md](docs/decisions/0013-ui-studio-react-flow.md) |
| D20 | Narrative stdout for non-technical readers | accepted | [0014-narrative-stdout.md](docs/decisions/0014-narrative-stdout.md) |
| D21 | Hierarchical Studio graph (L0/L1/L2 subgraph) | accepted | [0014-hierarchical-studio-graph.md](docs/decisions/0014-hierarchical-studio-graph.md) |
