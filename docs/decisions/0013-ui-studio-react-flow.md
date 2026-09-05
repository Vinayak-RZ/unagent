# ADR 0013 — Unagent Studio UI (React Flow viewer + playback + proposal edit)

## Context

Word-of-mouth needs a visual of the architecture graph, simulation run, and proposed flips. Editing customer source is forbidden (ADR 0003).

## Decision

Ship a local Vite + React + TypeScript Studio under `ui/` using React Flow (`@xyflow/react`) + ELK. Features: graph viewer, hierarchical enter/exit, simulation playback, in-graph **proposal** edit with export only. Design: `docs/design/DESIGN-meta.md` + impeccable `PRODUCT.md` / `DESIGN.md` (product register, light canvas, cobalt accent).

## Consequences

- Proposal edits never auto-apply to user agent source.
- UI consumes report JSON + simulation events; does not reimplement the advisor in TypeScript.
- CLI launcher: `python -m superdeterminism ui --report PATH`.
