# Determinism Advisor scaffold

> Copy these files by hand. Do not apply this patch to graph.py automatically. simulation != production; canary is confirmatory.

estimator: l0_tape_splice
evidence_ceiling: cassette

## code_agent — ABSTAIN
- n=14 &lt; n_min=30

## code_exec — ABSTAIN
- n=8 &lt; n_min=30

## data_agent — ABSTAIN
- n=8 &lt; n_min=30

## mcp_arxiv — ABSTAIN
- n=7 &lt; n_min=30

## mcp_warehouse — ABSTAIN
- n=4 &lt; n_min=30

## research_agent — ABSTAIN
- n=18 &lt; n_min=30

## skill_lint — ABSTAIN
- n=6 &lt; n_min=30

## sql_query — ABSTAIN
- n=4 &lt; n_min=30

## supervisor_gate — FlipToDet
- schema_ok=1.00 &gt;= 0.8
- p_mode=1.00 (wilson_lower=0.91) &gt;= 0.7
- L0 splice tail_stable

## task_router — ABSTAIN
- no rule fired with a CI that excludes the threshold

## web_search — ABSTAIN
- n=6 &lt; n_min=30
