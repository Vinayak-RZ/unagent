#!/usr/bin/env bash
# Regenerate Unagent CLI artifacts from demos/e2e-langgraph/traces.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
TR="demos/e2e-langgraph/traces.json"
OUT="demos/e2e-langgraph"

"$PY" -m superdeterminism validate "$TR"
"$PY" -m superdeterminism inspect "$TR" --adapter langgraph >"$OUT/inspect.json"
"$PY" -m superdeterminism recommend "$TR" --adapter langgraph --stdout json --json "$OUT/report.json" >/dev/null
"$PY" -m superdeterminism simulate "$TR" --adapter langgraph --mode report --json "$OUT/simulate.json" >/dev/null
"$PY" -m superdeterminism studio-report "$TR" --adapter langgraph --out "$OUT/studio_report.json"
"$PY" -m superdeterminism scaffold "$OUT/report.json" --out "$OUT/scaffold"
mkdir -p ui/public
cp "$OUT/studio_report.json" ui/public/e2e_studio_report.json
echo "pipeline ok → $OUT/studio_report.json"
