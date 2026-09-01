# Unagent product hardening — master execution plan

> Nawab project-mode contract. Approved 2026-09-01. Historical P1 plan: [docs/plans/p1-langgraph-plan.md](docs/plans/p1-langgraph-plan.md).

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | project |
| **Stack** | Python 3.10+, stdlib core, optional adapters, pytest |
| **Base branch** | `main` |
| **Feature branch** | `cursor/unagent-product-hardening` |
| **Authority** | AGENTS.md, docs/methodology.md, architecture.md, ingestion.md, `.specify/specs/001-product-hardening/` |
| **Estimated commits** | phase-grouped logical commits matching §9 |
| **Lead agent** | orchestrate, test, commit |

Product: **Unagent**. Package: `superdeterminism`. Repo: `Vinayak-RZ/unagent`. Offline OSS CLI + library. Research-complete before release.

## §1 North star & scope

**Objective:** A trustworthy offline advisor that reconstructs versioned agent graphs from production telemetry, evaluates determinism-class interventions with evidence tiers and replay anchors, abstains when evidence is incomplete, and emits reproducible reports plus manual scaffolds.

**P0:** fail-closed policy, strict ingest, graph, stratified evidence, L0 tape, certified recommendations, report schema, CI, examples.

**P1 defer:** live L1, GCJR execution beyond hypotheses, hosted UI, extra ecosystem sinks beyond ATIF + custom.

**Non-goals:** SaaS, auto-apply, LLM-judge attribution, inventing `gen_ai.*`, renaming the Python package.

## §2 Prerequisites & blockers

| Item | Status | Resolution |
|------|--------|------------|
| P1 archived | done | docs/plans/p1-langgraph-plan.md |
| Spec Kit | done | `.specify/` constitution + spec |
| Outcome contract | done | spec.md: advisor.outcome.success / --outcome-attr / not_supplied |
| OTel pin | done | ADR 0007; ingest pin + compatibility aliases |
| Folder rename | pending user | Cursor lock; origin already unagent |

## §3 Authority & artifact map

| Document | Role |
|----------|------|
| This file | execution contract |
| `.specify/specs/001-product-hardening/spec.md` | outcome + requirements |
| docs/methodology.md | estimator rules to implement |
| src/superdeterminism/ | writable implementation |
| tests/ | gates |
| schemas/ | report/tape contracts |

## §4 Architecture

See mermaid in the approved plan. Modules: `models`, `ingest`, `graph`, `evidence`, `replay`, `recommend` (via pipeline facade), `report`, `adapters`, `scaffold`, `cli`.

Trust: untrusted files, optional content, cassette-only L0, no source mutation.

## §5 Workstreams

WS-A docs/specs · WS-B ingest/graph · WS-C evidence/replay · WS-D recommend/UX · WS-E quality/release.

## §6 Orchestration

Lead implements. Parallel limit 2. Subagents optional; not required when the lead can finish a phase in-repo.

## §7 Phase map

0 spec → A fail-closed → B contracts → C ingest → D graph → E evidence → F replay → G policy → H product UX → I adapters → N hardening.

## §8 Todos

See agent todo list: phase-0 through phase-i-release.

## §9 Commit matrix

Phase 0: archive P1 · this plan · spec kit · landscape · ADRs.  
Phase A–N: fail-closed tests/fixes · contracts · ingest · graph · evidence · replay · policy · report/scaffold · adapters/CI.

## §10 Tests & CI

`python -m pytest -q`. Contract + negative + planted-truth + extras-free import hygiene. GitHub Actions Python 3.10–3.14.

## §11 Research log

See docs/landscape.md (2026-09-01) and DECISIONS D11–D15. CAR, Progressive Crystallization, RouteGuard, FlowScout, SymTrace, GCJR, OTel GenAI Aug–Sep 2026.

## §12 Doc sync

PROGRESS, PHASE_*_COMPLETION, LEARNING, DECISIONS, schemas, usage.

## §13 Gates

A: no unsafe FlipToDet. B: round-trip contracts. C: malformed fails closed. D: graph goldens. E: order-invariant strata. F: tape/tamper/diverge. G: policy matrix. H: e2e example. N: validate.ps1 twice.

## §14 Hardening

Static audit, full matrix, ponytail review, speckit-converge, `scripts/validate.ps1`.

## §15 Rollout

GitHub pre-release of `superdeterminism` after Phase N. No PyPI until user approval. No hosted cutover.

## §16 Exit criteria

P0: fail-closed; OTLP graphs; L0 replay vs resample; deltas + tier + provenance; tests pin methodology; clean install e2e; CI green.

## §17 Risks

False causal confidence → evidence ceilings. OTel drift → pin + aliases. Scope → P1 defer.

## §18 Execution protocol

Ponytail on every edit. One logical commit per slice. Tests in the same commit. Never weaken fail-closed for compatibility.
