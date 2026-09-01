# References

Bibliography for Unagent research. **Dated 2026-09-01.** Primary sources below were checked against arXiv HTML/abs and official repos on that date. Short labels (WHEN2TOOL, GCJR) are in-text only.

## Counterfactual replay and attribution

- Shah, J. et al. *Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures.* arXiv:2606.08275. https://arxiv.org/abs/2606.08275 — code: https://github.com/jaineet17/causal-agent-replay
- *CausalFlow: Causal Attribution and Counterfactual Repair for LLM Agent Failures.* arXiv:2605.25338. https://arxiv.org/abs/2605.25338 — code: https://github.com/devangb3/CausalFlow
- Tracefork. https://github.com/pratik916/tracefork
- AgentReplay. https://github.com/gadda00/agentreplay
- counterfact. https://github.com/counterfact-labs/counterfact
- Luan, Z. et al. *Repair or Resample? Rethinking Failure Debugging in LLM Multi-Agent Systems* (SymTrace). arXiv:2608.25920. https://arxiv.org/abs/2608.25920 (2026-08-26)
- *Localizing Emergent Failures in Agentic AI: Recovering Minimal Repair Families via Counterfactual Replay* (GCJR). arXiv:2608.29228. https://arxiv.org/abs/2608.29228 (2026-08-29)
- *Progressive Crystallization: Turning Agent Exploration into Deterministic, Lower-Cost Workflows in Production.* arXiv:2607.07052. https://arxiv.org/abs/2607.07052 (2026-07-08)
- *RouteGuard: Certifying Routing Gain in LLM Multi-Agent Systems.* arXiv:2608.07583. https://arxiv.org/abs/2608.07583 (2026-08-05)
- *FlowScout: From Execution Feedback to Reliable Tool-Using Agent Workflows.* arXiv:2608.10039. https://arxiv.org/abs/2608.10039 (2026-08-10)
- *IAPO.* arXiv:2608.24588. https://arxiv.org/abs/2608.24588 (2026-08-25)
- *ACES: Evaluating Skills, Not Just Agents.* arXiv:2608.20614. https://arxiv.org/abs/2608.20614 (2026-08-20)
- *HANSARD.* arXiv:2608.22512. https://arxiv.org/abs/2608.22512 (2026-08-23)

## Tool vs LLM (runtime, not architecture)

- *LLM Agents Already Know When to Call Tools — Even Without Reasoning* (WHEN2TOOL). arXiv:2605.09252. https://arxiv.org/abs/2605.09252
- *To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling.* arXiv:2605.00737. https://arxiv.org/abs/2605.00737

## Architecture search (offline workflows)

- *Multi-agent Architecture Search via Agentic Supernet* (MaAS). arXiv:2502.04180. https://arxiv.org/abs/2502.04180

## Observability and eval

- LangSmith + OpenTelemetry. https://docs.langchain.com/langsmith/trace-with-opentelemetry
- LangGraph time-travel. https://docs.langchain.com/oss/python/langgraph/use-time-travel
- LangChain agents (`create_agent`). https://docs.langchain.com/oss/python/langchain/agents
- AgentEvals. https://github.com/langchain-ai/agentevals
- MLflow LLM and Agent Evaluation. https://mlflow.org/docs/latest/genai/eval-monitor/
- DeepEval Tool Correctness. https://www.confident-ai.com/docs/metrics/single-turn/tool-correctness-metric — https://github.com/confident-ai/deepeval
- Langfuse OpenTelemetry. https://langfuse.com/integrations/native/opentelemetry
- Galileo Tool Selection Quality. https://docs.galileo.ai/concepts/metrics/agentic/tool-selection-quality

## OpenTelemetry GenAI

- Dedicated repo: https://github.com/open-telemetry/semantic-conventions-genai
- Pin used in [ingestion.md](ingestion.md): commit `c739977ae690961f36e435504e5c1febaef1f7f3` (2026-07-30)
- Core v1.42.0 move: https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.42.0
- Official LangChain instrumentor: https://pypi.org/project/opentelemetry-instrumentation-genai-langchain/
- Hodge, J. *The state of the OpenTelemetry GenAI semantic conventions (July 2026).* https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/
- Konishi, H. *OpenTelemetry GenAI Semantic Conventions Implementation Guide* (2026-08-02). https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html

## Nondeterminism

- Thinking Machines Lab. *Defeating Nondeterminism in LLM Inference.* https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/

## Foundations

- Pearl, J. *Causality.* 2nd ed., 2009. https://doi.org/10.1017/CBO9780511803161
