# Determinism Advisor scaffold

> Copy these files by hand. Do not apply this patch to graph.py automatically. simulation != production; canary is confirmatory.

estimator: l0_tape_splice
evidence_ceiling: cassette

## calculator — ABSTAIN
- no rule fired with a CI that excludes the threshold

## guard_input — FlipToDet
- schema_ok=1.00 &gt;= 0.8
- p_mode=1.00 (wilson_lower=0.91) &gt;= 0.7
- L0 splice tail_stable

## model — ABSTAIN
- observational/cassette incomplete (tier=observational, replay=diverged); FlipToDet requires L0 tail-stable splice
