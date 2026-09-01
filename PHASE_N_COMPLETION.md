# Phase N completion — product hardening

## Completed

Fail-closed `_decide`; strict ingest; graph reconstruction; stratified evidence; L0 cassette; report v1; validate/inspect/traces-dir; custom+atif adapters; scaffold refresh; examples; CI; SECURITY; changelog; validate.ps1.

## Files

`src/superdeterminism/{ingest,classify,graph,evidence,replay,pipeline,cli,scaffold,adapters/*}.py`, tests, `.github/workflows/ci.yml`, `schemas/report-v1.json`, `examples/`.

## Validation

`python -m pytest -q` plus `scripts/validate.ps1` (two consecutive greens). Import hygiene intact. Wheel job in `.github/workflows/ci.yml`.

## Outstanding

PyPI publish needs user approval. Live L1, Langfuse/MLflow/CrewAI extras remain P1/P2. Local folder rename to `unagent` still needs a closed Cursor window. macOS CI is deferred (Ubuntu+Windows matrix covers P0).

## What you learned

- Last-write kind on a pooled node_id is a correctness bug, not a shortcut.
- `error: "false"` must not count as failure.
- Scaffold reuse without wiping patches is a user-facing hazard.
