# How to improve this architecture

Grounded in `report.json` from **42 agent-as-model runs** (10 full delivery, 12 implement+review, 15 research, 5 policy-block). Simulation ≠ production.

| Node | Action | n | p_mode | Wilson lo | Evidence | Replay |
|------|--------|---|--------|-----------|----------|--------|
| `policy_gate` | ABSTAIN | 42 | 0.88 | 0.75 | observational | diverged |
| `supervisor` | ABSTAIN | 42 | 0.36 | 0.23 | observational | diverged |
| `delivery_orchestrator` | ABSTAIN | 42 | 0.36 | 0.23 | observational | diverged |
| `handoff` | ABSTAIN | 37 | 0.68 | 0.51 | observational | diverged |
| `research_agent` | ABSTAIN | 25 | 1.00 | 0.87 | cassette | tail_stable |
| `researcher` / tools | ABSTAIN | 25 | ≤0.60 | <0.70 | mixed | — |
| `implement_*` / `review_*` | ABSTAIN | 22 | — | — | n < 30 | — |

No FlipToDet this mix. That is the advisor working.

## Human-legible points

1. **Make `policy_gate` a function, not a model**  
   I first emitted free-text `reason` strings. Mode mass collapsed to **0.36**. Switching to `{allow, reason_code}` raised **p_mode to 0.88** (Wilson lo 0.75) — still **ABSTAIN**, because 5/42 runs are spend-denies and the L0 splice **diverged**. The gate is a rules table (`spend|refund|email` → deny; else allow). Implement it as a deterministic function. Canary: shadow on the same 42 tasks; promote only if allow/deny matches.

2. **Do not FlipToDet `supervisor` from this mix**  
   Four task types, four routes. p_mode 0.36 is the supervisor doing its job. Split “choose the next agent” into (a) a schema-stable intent classifier you *can* re-test with n≥30 per intent, and (b) a deterministic handoff table. Keep an LLM only for the leftover tail.

3. **Collect n≥30 per specialist before judging them**  
   Research ran 25 times, implement/review 22. Cassette-stable envelopes (`research_agent` p_mode=1.00) still ABSTAIN on n. Either run a research-only slice of 30+ or accept that a mixed orchestrator log is the wrong sampling unit for inner agents.

4. **Split each specialist LLM into plan vs commit**  
   `researcher` / `implementer` / `reviewer` tool-then-answer on one `node_id` → observational + diverged (same lesson as the old `model` node). One span for “which tool”, one for “final answer”. Then re-run L0 on the commitment span.

5. **Keep MCP search as a retriever; keep skills as tools**  
   `web_search` / `retrieve_docs` are `retriever` (`advisor.surface=mcp`). Do not FlipToDet an index. `read_file` / `apply_patch` (`surface=skill`) stay deterministic. **Harden `apply_patch`**: it is a write. Add a human checkpoint before apply (STRENGTHEN_SDB). Do not wrap it in an LLM.

6. **`handoff` is already the right class**  
   `transfer_to_*` is a router. ABSTAIN is correct. Drive it from the function in (2), not from a second model.

7. **Operational hygiene**  
   Pin GenAI semconv; record `advisor.schema_version` on import; never treat temperature=0 as a seed; treat this file as design evidence, not production proof. Scaffold under `scaffold/` is copy-by-hand only.

## What I changed after the first run

As the agent-as-model I replaced prose policy reasons with `reason_code`. That was the only cassette edit. The table above is the **after** report. The before report had `policy_gate` p_mode **0.36** for the same 42-task mix.
