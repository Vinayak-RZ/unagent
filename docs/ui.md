# Unagent Studio

Local React Flow studio for advisor reports.

## Generate a report

```bash
python -m superdeterminism studio-report examples/advisor_flip_to_det.json --out examples/studio_report.json --n-min 1
```

## Open Studio

```bash
cd ui && npm install && npm run dev
# or
python -m superdeterminism ui --report examples/studio_report.json --no-open
```

Load the JSON via the file picker or `?report=/absolute/path/to/report.json`.

## Proposal edits

In-graph proposal toggles are **drafts only**. Export JSON for review. Studio never writes agent source.
Simulation ≠ production.
