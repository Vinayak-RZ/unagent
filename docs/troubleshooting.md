# Troubleshooting

Exit `0` means a report was produced (including all-ABSTAIN). Exit `2` is bad input, unknown adapter, missing extra, or I/O failure.

| Symptom | Cause | What to do |
|---------|--------|------------|
| `unrecognized trace payload` | Not OTLP `resourceSpans` or `{traces:[{spans}]}` | `validate traces.json`; see [usage.md](usage.md) |
| All ABSTAIN with `n=1` | Default `--n-min 30` and Wilson lower bound | Expected. Use `examples/advisor_flip_to_det.json` for a FlipToDet demo |
| `unknown or mixed node kinds` | Unmapped `gen_ai.operation.name` or mixed ops on one node id | `inspect` the node map; do not guess |
| `failure_rate>0` on FlipToDet | Methodology: failure must not worsen | Fix the failing cluster first |
| `observational/cassette incomplete` | L0 splice not tail-stable | Need recorded I/O that the majority function still hits |
| `--adapter langgraph` exit 2 | Extra not installed | `pip install 'superdeterminism[langgraph]'` |
| Scaffold patches leftover | Reused `--out` | Hardened writer deletes stale `patches/*.diff` |

Privacy: message bodies are optional. Reports do not require content. Do not commit production traces with PII.
