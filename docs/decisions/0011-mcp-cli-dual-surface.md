# ADR 0011 — CLI-preferred dual agent surfaces (CLI / Python / MCP)

## Context

Agents in IDEs and CLIs need to call Unagent. Humans prefer a CLI. A hosted HTTP API adds ops cost without P0 value.

## Decision

Ship three surfaces over one library: preferred CLI (`python -m superdeterminism`), public Python API, and a stdio MCP server. MCP tools are thin wrappers; no recommend logic in the server. No public HTTP API in this release.

## Consequences

- MCP extra / entry point `unagent-mcp` (or `superdeterminism-mcp`).
- JSON stdout remains the agent contract when MCP is unavailable.
- Scaffold writes only under caller-supplied `out_dir`.
