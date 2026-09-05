# Subject project

| Field | Value |
|-------|-------|
| **Repo** | [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) (~4.4k★) |
| **Focus agent** | `research_assistant` (`src/agents/research_assistant.py`) |
| **Why this size** | Small multi-node LangGraph: guard → model ⇄ tools (or block). Not a monorepo product. |
| **License** | Apache-2.0 |

## Topology (faithful subset)

```text
guard_input
   ├─(safe)──► model ⇄ tools ──► END
   └─(unsafe)► block_unsafe_content ──► END
```

Unagent maps the `tools` / `execute_tool` span to node id `calculator` (tool name) via the LangGraph adapter.

## What this demo runs

`harness.py` reimplements that topology with:

- real **LangGraph** `StateGraph` + `ToolNode`
- **FakeMessagesListChatModel** (no paid API keys)
- a real **calculator** tool (same role as upstream `calculator`)

Each `graph.invoke` emits one Unagent-shaped trace (`langgraph_node` + `gen_ai.operation.name`). Default: **40** safe calculator runs so L0 can certify **FlipToDet** on the stable `guard_input` LLM gate.

Upstream code is **not** vendored; this harness is a runnable mirror for E2E testing only.
