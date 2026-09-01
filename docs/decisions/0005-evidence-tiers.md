# ADR 0005 — Evidence tiers and certification ceilings

- **Status:** accepted
- **Date:** 2026-09-01
- **Index:** [DECISIONS.md](../../DECISIONS.md) D11

## Context

Observational `p_mode` on pooled spans was enough to emit FlipToDet, including 100% failures and unknown ops. Methodology forbids that.

## Alternatives

- Keep observational FlipToDet with a disclaimer
- Require L1 live tail for any flip
- Evidence tiers with a ceiling: observational cannot certify a flip

## Decision

Tiers: `observational` < `cassette` < `interventional` < `production_confirmed`. FlipToDet / FlipToNondet require at least **cassette** (L0 splice tail-stable) plus methodology guards. Observational reports are diagnostics. L1 remains opt-in P1. Production confirmation is a canary checklist, not this process.

## Consequences

- Default estimator after hardening is `l0_tape_splice` when a cassette exists; otherwise `observational_l0_proxy` with ABSTAIN on flips.
- Reports carry `evidence_tier` and `evidence_ceiling`.
