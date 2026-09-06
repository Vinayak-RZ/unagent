# Learning

Phase notes per [learn-while-building](.cursor/skills/learn-while-building/SKILL.md). Two to four bullets each.

## Layered multi-agent Studio E2E (2026-09-06)

- A mixed orchestrator log is the wrong sampling unit for inner agents: research n=25 and implement n=22 both ABSTAIN at `n_min=30` even when the envelope is cassette-stable.
- Free-text policy reasons fragmented `policy_gate` to p_mode 0.36; `{allow, reason_code}` lifted it to 0.88 and Wilson lo 0.75 — still ABSTAIN because spend-denies make L0 diverge. Codes are necessary, not sufficient.
- Studio already had subgraph drill-down; the missing piece was `nest_for_studio` plus *not* hoisting recommendation ids onto the root. Without that guard, Layer 0 looked like a flat tool pile.
- `transfer_to_research_agent` was classified as a retriever because `"search" in tool`. Handoff must win before the substring check.

## Product hardening (2026-09-01)

- Observational `p_mode` is not a counterfactual. Cassette-stable L0 splice is the lowest tier that may FlipToDet.
- Trace-as-sampling-unit plus mixed-kind sets beats last-write classification; order no longer flips the advice.
- Progressive Crystallization and FlowScout force a narrower claim: re-typing on the ingested graph, not auto-promotion or workflow search.
- Control-edge targets must not inherit ROUTER kind; that mixed the destination LLM node and blocked FlipToDet.


## Vendor README skills (2026-08-17)

- The `readme` skill chooses; it does not write. Product landing stays in `README.md`. Extensive is a companion at `docs/EXTENSIVE.md`, never the GitHub front door unless the user overrides.
- Re-vendoring `skills-manifest.json` from upstream would restore `docs/MCP_SETUP.md` paths. D3 remaps to `docs/cursor-config/` must be merged by hand.
- An ABSTAIN CLI capture (`n=1`, Wilson lower 0.21) teaches the product better than a fixture that always flips.
- Copy, not symlink: Cloud Agents only see skills that are committed in this repo ([`.cursor/VENDOR.md`](.cursor/VENDOR.md)).

## Phase R — Revise done work (2026-08-15)

- A README that links files that do not exist is a documentation bug, not a roadmap. [documentation.mdc](.cursor/rules/documentation.mdc) requires the front door to match the tree.
- nawab + documentation.mdc want root `PROJECT_OVERVIEW.md` and `DECISIONS.md` even on a docs-only repo. A thin `PROGRESS.md` is not enough.
- Vendoring cursor-config-coding into `docs/` mixed two audiences. Moving guides to `docs/cursor-config/` and fixing every relative link in rules/skills was the real cost of the move.
- extensive-readme must skip empty API/test/deploy sections. Inventing a CLI here would violate the skill’s “do not invent features” rule.

## Phase A — Research docs (2026-08-15)

- The useful product sentence is narrower than “counterfactual simulation.” CAR already owns `do_policy`; our gap is *re-typing* the node, not intervening on a step.
- OTel GenAI is usable as interchange and unusable as a domain model: no determinism class, no handoff, conditional edges often have no span. `advisor.*` / `det.*` are mandatory.
- L0 is honest only if ABSTAIN is first-class. A report that always recommends a flip would be a judge in disguise.
- LangGraph v0 is `create_agent` + `langgraph_node`, not the word “agent” and not deprecated `create_react_agent`.

## P0 — Agnostic core (2026-08-15)

- Splitting “LangGraph first” vs “agnostic core first” is the load-bearing product decision. Core with zero framework deps is the only way P2 (CrewAI / MAF / raw agents) stays honest.
- Agents need JSON stdout and exit-2-on-bad-input more than they need a pretty TUI.
- `n_min=30` plus Wilson lower-bound stops a 30-identical-JSON fixture from looking more confident than it is when n is small; tests pass `--n-min` explicitly.

## P1 — LangGraph adapter (2026-08-15)

- The mapper does not need to import LangChain. Pins + `find_spec` are enough for `--adapter langgraph` presence; attribute rewrite is the whole adapter.
- Python binds `adapters.langgraph` onto the parent package after a submodule import. “Lazy” is “`__init__.py` does not import it,” not “`sys.modules` stays empty.”
- `create_react_agent` as a forbidden *token* in `src/` fights the “do not use this API” warning. Say “deprecated ReAct prebuilt” in docs; keep the token out of source and out of emitted diffs.
- Extras-on pytest skips the missing-extra exit-2 tests. Both modes are required: extras-free for that path, extras-on for `--adapter langgraph` end-to-end.

## P1 / P2 specs (2026-08-15)

- Specifying adapters *before* code is what keeps the core honest: P1 is allowed one LangGraph file; P2 is when a `Protocol` is justified (second adapter).
- P1 must not fork the recommender. If the mapper cannot produce P0 `Trace`s, the adapter is wrong — not the decision rules.
- P2 “done” is pluggability (custom example + at least one non-Lang path), not “we ingested one more Lang sink.”

## Phase N — Validate (2026-08-15)

- S2 found zero FIX-class claim-hygiene hits and no broken relative links. The “do not say” sentences are easy to grep as false positives; keep them in dedicated sections.
- Front-door links only work if you wait until the files exist (Phase R) and then re-link (commit 7). Doing both at once is how the first README went stale.
- Research docs stayed well under 400 lines because citations live in `docs/references.md`.
