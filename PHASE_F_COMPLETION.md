# Phase F completion — L0 replay

## Completed

Hash-verified tape 1.0, splice, tail-stability, tamper detection, mutating-call refusal. Cassette tier only when splice is tail-stable on a non-mixed node. Observational pooling is `resample_only`.

## Validation

`tests/test_replay.py`.

## What you learned

- Replay vs resample is a report field, not a comment.
