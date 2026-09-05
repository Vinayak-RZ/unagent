# Unagent Studio

Local React Flow UI for viewing advisor reports, playing simulation events, and exporting **proposal drafts** (never auto-applied).

## Run

```bash
cd ui
npm install
npm run dev
```

Generate a sample report:

```bash
python -m superdeterminism studio-report examples/advisor_flip_to_det.json --out examples/studio_report.json
```

Open Studio and load `examples/studio_report.json`, or:

```bash
python -m superdeterminism ui --report examples/studio_report.json
```

## Design

See [docs/design/STUDIO_SHAPE.md](../docs/design/STUDIO_SHAPE.md), [PRODUCT.md](../PRODUCT.md), [DESIGN.md](../DESIGN.md).
