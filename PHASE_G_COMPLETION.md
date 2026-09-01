# Phase G completion — policy

## Completed

Fail-closed `_decide`: FlipToDet requires cassette + tail-stable + schema/p_mode/Wilson + metric delta + completeness/trust + single workload cell. FlipToNondet needs L1. Bounded AND pair hypotheses on adjacent failing nodes (GCJR-shaped, not executed).

## Validation

Policy tests in `tests/test_pipeline.py`.

## What you learned

- Observational p_mode is not a counterfactual.
