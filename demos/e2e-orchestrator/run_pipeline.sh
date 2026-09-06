#!/usr/bin/env bash
# Regenerate Unagent CLI artifacts from demos/e2e-orchestrator/traces.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
TR="demos/e2e-orchestrator/traces.json"
OUT="demos/e2e-orchestrator"

"$PY" demos/e2e-orchestrator/harness.py --n 40 --out "$TR"
"$PY" -m superdeterminism validate "$TR"
"$PY" -m superdeterminism inspect "$TR" >"$OUT/inspect.json"
"$PY" -m superdeterminism recommend "$TR" --stdout json --json "$OUT/report.json" >/dev/null
"$PY" -m superdeterminism simulate "$TR" --mode report --json "$OUT/simulate.json" >/dev/null
"$PY" -m superdeterminism studio-report "$TR" --out "$OUT/studio_report.json"
"$PY" -m superdeterminism scaffold "$OUT/report.json" --out "$OUT/scaffold"
mkdir -p ui/public
cp "$OUT/studio_report.json" ui/public/e2e_orchestrator_studio_report.json
echo "pipeline ok → $OUT/studio_report.json"
