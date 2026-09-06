# ADR 0014 — Hierarchical Studio graph (L0 → L1 → L2)

## Context

Unagent Studio supports breadcrumb drill-down via `children` / `subgraph` on graph nodes, but `studio-report` only emitted a flat `graph.nodes` list. The e2e-langgraph demo (3 nodes) was insufficient to demonstrate orchestrator → agent → tool/MCP layering.

## Decision

1. Emit **`advisor.layer`** (`L0` | `L1` | `L2`) and optional **`advisor.parent_agent`** on trace span attributes (advisor-owned fields per claim hygiene).
2. Add `graph_hierarchy.nest_for_studio()` to wrap flat `inspect_traces` output into nested `subgraph` structures:
   - **L0** nodes at the root frame (orchestrator / `task_router`).
   - **L1** specialist agents as `subgraph` children of L0.
   - **L2** tools, MCPs, and skills as `subgraph` children of their owning L1 agent.
3. `studio-report` calls hierarchy nesting and attaches a **`narrative`** markdown string with human-readable improvement bullets.
4. Simulation events gain **`layer_enter`** and **`assign_task`** kinds for cinematic playback (orchestration → assignment → in-agent splice).

## Consequences

- Flat `reconstruct()` and recommend pipeline unchanged; hierarchy is a Studio presentation layer.
- Demos must tag spans consistently; adapters can map framework metadata to `advisor.layer` later.
- Report schema remains backward compatible (additive fields).

## Alternatives considered

- UI-only grouping by node name prefix — rejected; duplicates logic and breaks drill-down without backend contract.
- Separate graph file per layer — rejected; breadcrumbs need single report artifact.
