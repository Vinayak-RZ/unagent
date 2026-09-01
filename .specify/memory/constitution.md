# Unagent Constitution

**Version:** 1.0.0  
**Ratified:** 2026-09-01  
**Last amended:** 2026-09-01

## Principles

### I. Fail closed

Unknown, mixed, incomplete, low-trust, or replay-divergent evidence **ABSTAINs** or **STRENGTHEN_SDB**. Never emit FlipToDet / FlipToNondet from observational pooling alone.

### II. Honest estimators

Label every number **observational**, **cassette (L0)**, **interventional (L1)**, or **production-confirmed**. Simulation ≠ production. A canary with the same outcome vector is confirmatory.

### III. Agnostic core

`src/superdeterminism/` except `adapters/<framework>.py` has zero LangChain / LangGraph / CrewAI / MAF imports. Adapters translate; one recommender decides.

### IV. No auto-apply

Reports and scaffolds are suggestions. Never rewrite customer `graph.py`, open a PR, or execute side effects.

### V. Advisor-owned fields

Never invent `gen_ai.*`. Persist `advisor.*` / `det.*`. Pin OpenTelemetry GenAI by **commit**, not tag. Conventions remain Development.

### VI. Differentiation

Counterfactual *re-typing* of nodes on an ingested production graph — not scoring the path already run, not searching a new workflow, not generic trace-driven determinization.

### VII. Stdlib runtime

Core dependencies stay empty unless an ADR records a runtime library. Tests and CI tools may live in extras.

### VIII. Privacy by default

Trace files are untrusted input. Message bodies are optional. Reports redact content. No network on the default path.
