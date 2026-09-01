# Phase B completion — contracts

## Completed

Versioned dataclasses: schema/report/tape 1.0, evidence tiers, replay status, ArchitectureGraph, Recommendation provenance fields. Pipeline is a facade over ingest/graph/evidence/replay.

## Validation

Report JSON includes `report_version`, `evidence_tier`, `replay_status`. Schemas in `schemas/`.

## What you learned

- Observational evidence is a labeled ceiling, not a FlipToDet certificate.
