# ADR 0006 — Versioned report and advisor schema

- **Status:** accepted
- **Date:** 2026-09-01
- **Index:** [DECISIONS.md](../../DECISIONS.md) D12

## Context

Reports had no `report_version`. `advisor.schema_version` was documented and unimplemented.

## Decision

- `advisor.schema_version` = `1.0` on ingest metadata and reports.
- `report_version` = `1.0` in JSON reports (`schemas/report-v1.json`).
- Tape format `tape_version` = `1.0`.
- Readers must reject unknown major versions.

## Consequences

Additive fields in 1.x are allowed. Breaking changes bump major and keep a compatibility reader only if tests exist.
