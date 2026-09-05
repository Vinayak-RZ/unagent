# ADR 0012 — Dual-mode sinks (file export + live pull)

## Context

Frictionless traces→advice requires both offline dumps and live observability pulls (Langfuse, LangSmith, MLflow).

## Decision

Implement sinks with two modes each: file/export ingest and live API client (env credentials). `--sink` fetches; `--adapter` maps. Core stays extras-free; sink clients live behind optional extras. CI uses VCR/fixtures — no live network required.

## Consequences

- Package layout `superdeterminism/sinks/{langfuse,langsmith,mlflow}.py`.
- File path always works even if live clients slip.
- Never invent `gen_ai.*` keys; map vendor fields into existing Trace/Span model.
