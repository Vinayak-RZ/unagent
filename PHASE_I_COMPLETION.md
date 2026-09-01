# Phase I completion — adapters and release gates

## Completed

Adapter Protocol: langgraph (extra), custom, atif (no extra). `--traces-dir`. CI Python 3.10–3.14 on Ubuntu/Windows plus wheel install job. `scripts/validate.ps1`, SECURITY, CHANGELOG.

## Validation

`tests/test_adapters_extra.py`, extras-free import hygiene.

## Outstanding

PyPI publish needs explicit approval. Live L1 remains P1.

## What you learned

- `Protocol` must come from `typing` on Python 3.14.
