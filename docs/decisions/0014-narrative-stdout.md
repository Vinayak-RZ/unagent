# ADR 0014 — Narrative stdout for non-technical readers

## Context

Machine JSON serves agents. Executives and PMs need plain-language advice without Wilson jargon.

## Decision

Add `--stdout narrative` (and MCP equivalent) rendering the same report into short prose: what we found, what we recommend or why we abstain, and that simulation ≠ production. Does not change decide rules.

## Consequences

- New `superdeterminism.narrative` renderer.
- Golden fixture tests for tone and claim hygiene.
