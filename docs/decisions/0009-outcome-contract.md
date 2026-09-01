# ADR 0009 — User-supplied outcome contract

- **Status:** accepted
- **Date:** 2026-09-01
- **Index:** [DECISIONS.md](../../DECISIONS.md) D15

## Context

Methodology’s outcome vector includes task success and policy compliance. Traces often lack them. Using `not error` as success is a proxy lie.

## Decision

See `.specify/specs/001-product-hardening/spec.md`. Task success from `advisor.outcome.success` or `--outcome-attr`. Otherwise `null` / `not_supplied`. `span.error` feeds `failure_rate` only. Policy from `advisor.outcome.policy_ok` plus name-based hard override.

## Consequences

FlipToDet can still fire on cassette-stable schema + non-worsening failure + cost/latency/auditability improvement. It must not claim task-success delta unless the contract is present.
