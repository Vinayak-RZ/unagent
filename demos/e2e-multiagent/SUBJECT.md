# Subject — Delivery Orchestrator (agent-as-model)

| Field | Value |
|-------|-------|
| **Shape** | LangGraph supervisor + three compiled specialist subgraphs + policy gate |
| **Why this size** | The research-assistant E2E is one LLM and one tool. This subject has orchestration, handoffs, MCP, skills, and a spend gate. |
| **Model** | The lead Cursor agent authored every routing and tool I/O blob (D22). Harness replays the cassette. No paid API. |
| **License** | Apache-2.0 (this repo) |

## Layer 0 — orchestration

```text
delivery_orchestrator
  supervisor ──handoff──► research_agent
            ──handoff──► implement_agent
            ──handoff──► review_agent
            ───────────► policy_gate
```

## Layer 1 — specialists

| Agent | LLM | Surfaces |
|-------|-----|----------|
| `research_agent` | `researcher` | `web_search` (MCP), `retrieve_docs` (retriever), `cite_sources` (tool) |
| `implement_agent` | `implementer` | `read_file` (skill), `apply_patch` (skill, side-effect), `run_tests` (tool) |
| `review_agent` | `reviewer` | `lint` (tool), `security_scan` (tool) |

## Agent-as-model reasoning (this run)

### `research_query`

User: *In one sentence, what is Unagent's FlipToDet rule?*

I am the supervisor: read-only methodology question, no patch, no spend. Hand off to `research_agent` only, then `policy_gate`.

I am the researcher: I will not invent the rule. Call `web_search` (MCP) for the product sentence, `retrieve_docs` on `docs/methodology.md`, `cite_sources`, then one commitment sentence.

I am the policy gate: `{allow: true, reason: "read-only knowledge question"}`.

### `implement_constant`

User: *Add a named constant for the default n_min so callers do not pass a magic 30.*

Supervisor: local refactor. Route `implement_agent` → `review_agent` → `policy_gate`.

Implementer: `read_file` `src/superdeterminism/pipeline.py`. `N_MIN_DEFAULT = 30` is already there. `apply_patch` records “already named”; `run_tests` pass.

Reviewer: lint clean; security_scan no secrets.

Policy: allow — no spend.

### `full_delivery`

User: *Should the classify node be a function? If the advisor would FlipToDet, draft only the helper name.*

Supervisor: need the rule (research) then a naming artifact (implement) then review.

Researcher: same tool chain; conclude FlipToDet applies when schema + mode + L0 tail-stable.

Implementer: `read_file` classify.py; `apply_patch` proposes `classify_as_function`; tests pass.

Policy: allow.

### `policy_block`

User: *Issue a $500 refund to customer 99 and email the receipt.*

Supervisor: spend + email. Do **not** hand off to implement. `policy_gate` only.

Policy: `{allow: false, reason: "refund/spend/email requires a human checkpoint"}`.

## What the demo runs

`harness.py` builds the real LangGraph, executes tools, and emits Unagent-shaped traces (`langgraph_node`, `gen_ai.operation.name`, `advisor.surface`). Default mix ≥30 runs so L0 can speak.

Upstream code is not vendored. Simulation ≠ production.
