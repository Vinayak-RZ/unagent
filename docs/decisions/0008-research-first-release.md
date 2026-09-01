# ADR 0008 — Research-complete before public release

- **Status:** accepted
- **Date:** 2026-09-01
- **Index:** [DECISIONS.md](../../DECISIONS.md) D14

## Context

User chose research-first: do not release until graph reconstruction and L0 replay exist.

## Decision

No GitHub/PyPI product release until Phase N exit criteria pass. Experimental CLI in-repo is allowed. Observational proxy may remain as a labeled diagnostic path; it cannot certify flips.

## Consequences

README must not imply production-ready architecture advice until the cassette estimator is the default recommend path.
