# Spec: Unagent product hardening

**Feature:** research-complete offline determinism advisor  
**Date:** 2026-09-01  
**Status:** approved for implementation

## Problem

P0/P1 ship a CLI that can recommend `FlipToDet` from historical output-mode statistics. That contradicts [docs/methodology.md](../../../docs/methodology.md): unknown nodes must abstain, FlipToDet needs failure-safety and a metric improvement, and L0 is a hash-verified tape splice on a reconstructed graph.

## Outcome contract (user-supplied Y)

Task success and policy compliance enter the outcome vector only from:

1. Span attribute `advisor.outcome.success` (bool / 0 / 1) on the workflow/root span, **or**
2. CLI `--outcome-attr NAME` naming a boolean/numeric attribute, **or**
3. Explicit absence: `task_success` is `null` and labeled `not_supplied`.

Default `span.error` inversion is a **failure proxy**, never a task-success claim. Actionable FlipToDet may use cassette-stable schema/failure/cost/latency/auditability; it MUST NOT claim task-success improvement unless (1) or (2) is present with `n >= n_min`.

Policy compliance uses `advisor.outcome.policy_ok` the same way, plus the hard override on commit/spend/PII/auth node ids.

## User stories

1. As an agent, I ingest OTLP JSON and get a versioned JSON report or exit 2.
2. As a human, I run `validate` / `inspect` before `recommend`.
3. As a LangGraph user, I use `--adapter langgraph` then `scaffold` without source mutation.
4. As a custom-stack user, I copy `examples/custom_adapter.py`.

## Requirements

- Fail-closed `_decide` (unknown, mixed, failed, incomplete, observational-only).
- Normalized spans with IDs, timing, real OTLP status, capture flags.
- Architecture graph with edges, completeness, trust, point-of-commitment.
- Stratified evidence (trace as sampling unit).
- Hash-verified L0 cassette, anchors, splice, mutating-call refusal.
- Report schema v1 with provenance, evidence tier, replay status, canary checklist.
- Adapter Protocol + `--traces-dir` + ATIF example + custom example.
- CI, examples, troubleshooting, SECURITY, changelog.

## Non-goals

Hosted SaaS, auto-apply, default L1/L2, LLM-judge attribution, renaming package `superdeterminism`.
