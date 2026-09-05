# E2E report — LangGraph research assistant × Unagent Studio

**Date:** 2026-09-05  
**Operator:** Cursor cloud agent (this run)  
**Product:** Unagent (`superdeterminism`) + Unagent Studio (`ui/`)  
**Subject:** [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) `research_assistant` topology  
**Artifacts:** [demos/e2e-langgraph/](../../demos/e2e-langgraph/) · media in [docs/assets/e2e/](../assets/e2e/)

> Simulation ≠ production. Scaffold patches are illustrative and never auto-applied.

## 1. Objective

Prove the full Unagent loop on a **real LangGraph architecture** (not only fixture JSON):

1. Run a faithful multi-node graph.
2. Emit traces.
3. Reconstruct the graph (`inspect`).
4. Recommend + L0-simulate (`recommend` / `simulate` / `studio-report`).
5. Open Studio, capture the architecture graph and simulation playback.
6. Document how to improve that architecture.

## 2. Subject architecture

Upstream agent (`research_assistant`) is a compact LangGraph:

```text
guard_input
   ├─(safe)──► model ⇄ tools ──► END
   └─(unsafe)► block_unsafe_content ──► END
```

This demo’s harness (`demos/e2e-langgraph/harness.py`) mirrors that topology with:

- real LangGraph `StateGraph` + `ToolNode`
- `FakeMessagesListChatModel` (no paid API keys)
- a real `calculator` tool

**Why this repo:** popular (~4.4k★), small enough to reason about, multi-node (not a toy single LLM call), Apache-2.0.

## 3. Method

```bash
pip install -e ".[dev,langgraph]"
python demos/e2e-langgraph/harness.py --n 40 --out demos/e2e-langgraph/traces.json
./demos/e2e-langgraph/run_pipeline.sh
# Studio
cp demos/e2e-langgraph/studio_report.json ui/public/e2e_studio_report.json
cd ui && npm install && npm run dev
# http://127.0.0.1:5173/?report=/e2e_studio_report.json
```

Forty identical safe calculator runs produce enough sample size for default `n_min=30` and Wilson lower-bound checks.

## 4. Reconstructed graph (Studio)

![Architecture graph in Unagent Studio](../assets/e2e/studio_graph_architecture.png)

| Node (as mapped) | Kind | Role |
|------------------|------|------|
| `guard_input` | `llm_reasoner` | Safety gate (LLM-shaped in upstream; stable JSON here) |
| `model` | `llm_reasoner` | Tool-calling reasoner |
| `calculator` | `deterministic_tool` | ToolNode / `execute_tool` (adapter maps tool name) |

## 5. Simulation playback

![Simulation mid-playback (9/15)](../assets/e2e/studio_simulation_playback.png)

<video src="../assets/e2e/studio_simulation_playback.mp4" controls></video>

L0 cassette events advance through load → graph → cassette → splice → decide for ranked nodes. Status line in the mid-playback frame: `splice: tail_stable @ guard_input` at step **9 / 15**.

## 6. Advisor recommendations (actual report)

From `demos/e2e-langgraph/report.json`:

| Node | Action | n | p_mode | Wilson lo | Evidence | Replay |
|------|--------|---|--------|-----------|----------|--------|
| `guard_input` | **FlipToDet** | 40 | 1.00 | 0.91 | cassette | tail_stable |
| `model` | ABSTAIN | 40 | 1.00 | 0.91 | observational | diverged |
| `calculator` | ABSTAIN | 40 | 1.00 | 0.91 | cassette | tail_stable |

**Why FlipToDet on `guard_input`:** schema_ok=1.00, mode mass=1.00 with Wilson lower ≥ 0.7, L0 splice tail-stable, and estimated cost/latency deltas from removing the model wait.

**Why ABSTAIN on `model`:** within each trace the node emits two different outputs (tool call, then final answer). Cassette splice diverges → FlipToDet is refused even though the point estimate looks perfect.

**Why ABSTAIN on `calculator`:** already deterministic; no flip rule fires.

## 7. How to improve this architecture

Grounded in the advisor output + graph structure (not generic advice):

1. **Replace `guard_input` with a deterministic function**  
   FlipToDet is certified at cassette tier for this traffic. Implement the scaffold under `demos/e2e-langgraph/scaffold/` (copy by hand). Keep the node name so wiring stays stable. Canary: shadow the function on the same inputs; promote only if outcome vector holds.

2. **Do not FlipToDet `model` from these traces**  
   ABSTAIN is correct. To re-evaluate, either split “tool-planning” vs “final answer” into separate nodes, or emit one commitment span per decision with stable schema. Re-run with n≥30 per commitment node.

3. **Keep `calculator` as a tool**  
   It is already the right determinism class. Optionally STRENGTHEN_SDB only if you add side effects / network later.

4. **Operational hygiene**  
   Pin GenAI semconv / LangGraph instrumentation versions; record `advisor.schema_version` on imports; never treat temperature=0 as a seed; treat this simulation as design evidence, not production proof.

## 8. Claim hygiene

- This run used **executed** LangGraph invokes (fake chat model), not hand-authored one-off fixtures only.
- Evidence ceiling is **cassette L0**, not live L1.
- Unagent never rewrote the subject `graph.py`.
- Studio proposal toggles are drafts; export only.

## 9. Reproduce

See [demos/e2e-langgraph/README.md](../../demos/e2e-langgraph/README.md). Regression: `pytest tests/test_e2e_langgraph_demo.py`.
