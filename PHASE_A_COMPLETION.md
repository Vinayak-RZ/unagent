# Phase A completion — fail-closed

## Completed

Unsafe recommendation regressions: unknown, mixed (order-invariant), 100% failed LLM, DET failures ABSTAIN for FlipToNondet. CLI exit 2 on malformed input. Scaffold wipes stale patches. Docs match implemented status.

## Validation

`tests/test_pipeline.py`, `tests/test_cli_hardening.py`.

## What you learned

- Last-write kind on a pooled node_id is a correctness bug.
- STRENGTHEN_SDB is the fail-closed action for commit/spend/PII paths.
