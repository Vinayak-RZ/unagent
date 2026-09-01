# Privacy

Unagent runs locally on files you provide. It does not upload traces.

| Data | Default |
|------|---------|
| Span names / node ids | Copied into reports |
| Inputs / outputs | Optional; used for L0 cassette when present |
| Tokens / latency | Aggregated in reports |
| Secrets in attributes | Not scanned; treat traces as sensitive |

No `cron.md` / hosted jobs. No emails. Automation is the CLI only — suggestions, never side effects ([0003-no-auto-apply.md](decisions/0003-no-auto-apply.md)).
