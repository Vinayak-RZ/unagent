#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO="$ROOT/demos/e2e-multiagent"
cd "$ROOT"
python3 "$DEMO/harness.py" --n "${N:-42}" --out "$DEMO/traces.json"
python3 -m superdeterminism recommend "$DEMO/traces.json" --stdout json --n-min "${NMIN:-30}" \
  --json "$DEMO/report.json" >/dev/null
python3 -m superdeterminism simulate "$DEMO/traces.json" --mode report --n-min "${NMIN:-30}" \
  --json "$DEMO/simulate.json" >/dev/null
python3 -m superdeterminism studio-report "$DEMO/traces.json" --n-min "${NMIN:-30}" \
  --out "$DEMO/studio_report.json"
python3 -m superdeterminism scaffold "$DEMO/report.json" --out "$DEMO/scaffold"
mkdir -p "$ROOT/ui/public"
cp "$DEMO/studio_report.json" "$ROOT/ui/public/e2e_multiagent_studio_report.json"
echo "studio: http://127.0.0.1:5173/?report=/e2e_multiagent_studio_report.json"
