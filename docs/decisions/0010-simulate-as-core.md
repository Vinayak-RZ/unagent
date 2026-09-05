# ADR 0010 — Simulation as a core product surface

## Context

L0 cassette splice lived only inside `recommend`. The product differentiator is designing and running counterfactual determinism-class simulations on ingested architectures.

## Decision

Expose a first-class `simulate` API and CLI (`what-if`, `design`) that wraps and extends L0 replay. `recommend` delegates to the same evidence path. Opt-in L1 (`--opt-in-l1`) stays off by default.

## Consequences

- New module `superdeterminism.simulate` and CLI subcommand `simulate`.
- Simulation event stream feeds the Studio UI playback.
- Observational pooling alone still cannot certify FlipToDet.
