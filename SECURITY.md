# Security

- Trace files are untrusted. Size, span-count, and nesting limits apply (`ingest.py`).
- Default path is offline: no network, no model calls, no execution of recorded tools.
- Do not put secrets in traces you share. Reports redact nothing from `node_id`; treat node names as potentially sensitive.
- Scaffold never edits customer source.
- Report vulnerabilities privately via GitHub security advisories on [Vinayak-RZ/unagent](https://github.com/Vinayak-RZ/unagent).
