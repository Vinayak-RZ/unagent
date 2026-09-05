# PRODUCT.md — Unagent

> Impeccable product context. Register: **product** (tool UI, not brand marketing site).

## Product purpose

Unagent (package `superdeterminism`) is a design-time determinism advisor for agentic architectures. It ingests production traces, reconstructs the agent graph, runs counterfactual determinism-class simulations (tool ↔ LLM/subagent), and recommends a refactor with evidence — or **ABSTAINs**.

## Users

| Persona | Job | Mindset |
|---------|-----|---------|
| Agent engineer | Decide where to flip LLM nodes to tools | Focused, skeptical of hype |
| Platform / MLOps | Pull traces from Langfuse/LangSmith/MLflow | Time-poor, wants one command |
| IDE agent (MCP/CLI) | Call recommend/simulate as tools | Needs strict JSON schemas |
| Eng manager / PM | Read whether a flip is justified | Non-technical; hates jargon |

## Product principles

1. **ABSTAIN is a feature** — never invent certainty.
2. **Simulation ≠ production** — canary confirms.
3. **No auto-apply** — scaffolds and proposals only.
4. **CLI preferred** — MCP and Python wrap the same library.
5. **Fail closed** — incomplete evidence → ABSTAIN.

## Anti-references

- Purple-glow “AI dashboard” aesthetics
- Auto-rewriting customer `graph.py`
- Pretending observational pooling certifies a flip
- Hero-metric SaaS card grids as the Studio shell

## Studio scene (theme sentence)

An engineer at a bright daytime desk opens Unagent Studio to trust a flip recommendation before a canary — calm white canvas, cobalt accent for primary actions and live sim focus, ink for structure. Not a neon ops wall.

## Register

`product`
