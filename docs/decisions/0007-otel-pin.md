# ADR 0007 — OpenTelemetry GenAI commit pin and aliases

- **Status:** accepted
- **Date:** 2026-09-01
- **Index:** [DECISIONS.md](../../DECISIONS.md) D13
- **Amends:** [0001-otel-ingest.md](0001-otel-ingest.md)

## Context

Conventions remain **Development**. Between 2026-08-20 and 2026-09-01 upstream added usage breakdowns, restricted cache tokens on internal agent spans, and made `gen_ai.response.finish_reasons` authoritative.

## Decision

Keep ingest authority pin `c739977ae690961f36e435504e5c1febaef1f7f3` (2026-07-30) as the documented mapping baseline. Accept **compatibility aliases** only:

- tokens: `gen_ai.usage.input_tokens` / `prompt_tokens` (coalesce, never sum)
- cache/reasoning token attrs if present; do not copy client cache metrics onto internal agent spans
- finish: `gen_ai.response.finish_reasons` over per-message `finish_reason`

Do not silently track `main`. Bump the pin only with a fixture update and this ADR amendment.

## Consequences

Producer registry records which aliases fired. Unknown ops stay `UNKNOWN` + ABSTAIN.
