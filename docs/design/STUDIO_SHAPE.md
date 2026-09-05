# STUDIO_SHAPE.md — Unagent Studio layout brief

Product register: light canvas (`#F7F9FC`), cobalt accent (`#0064E0`) for primary actions and active simulation focus. No purple glow, glassmorphism, side-stripe cards, or gradient text.

## Shell

```
┌ Header: title · Load report · Close ─────────────────────────────┐
│ disclaimer strip (simulation != production)                      │
├────────────────────────────── graph canvas ────┬── inspector rail │
│ breadcrumbs (hierarchical enter/exit)          │ evidence + Wilson│
│ @xyflow/react + ELK layout                     │ proposal toggles   │
│ cobalt ring on playback-active node            │ export JSON CTA    │
├ playback strip: ← Step · Play/Pause · Step → ──┴──────────────────┤
```

## Data flow

1. **In:** report JSON via file picker or `?report=` URL (from `studio-report` or `simulate --mode report`).
2. **Graph:** `graph.nodes` / `graph.edges` when present; else synthesize nodes from `recommendations` (isolated if no edges).
3. **Hierarchy:** nodes with `children` or `subgraph` push a breadcrumb frame; back pops.
4. **Playback:** `simulation_events[]` stepped or auto-advanced; highlights `node_id` on the active event.
5. **Proposal:** per-node FlipToDet / STRENGTHEN_SDB / ABSTAIN toggles → download `*-proposal.json` (never auto-apply).

## Empty / error / loading

| State | Teaches |
|-------|---------|
| Empty | `studio-report` / `simulate --mode report`; sample `examples/studio_report.json` |
| Loading | Filename being parsed |
| Error | Missing `recommendations`; CLI to regenerate |

## Stack

Vite · React · TypeScript · `@xyflow/react` · `elkjs` · Vitest for reducer/playback.
