#!/usr/bin/env bash
# Unagent validation orchestrator — offline, no live network required.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

#!/usr/bin/env bash
# Unagent validation orchestrator — offline, no live network required.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

echo "==> [1/7] import hygiene"
PYTHONPATH=src "$PY" -m pytest -q tests/test_import_hygiene.py

echo "==> [2/7] pytest (extras-free)"
PYTHONPATH=src "$PY" -m pytest -q

echo "==> [3/7] simulate + sinks fixtures + mcp"
PYTHONPATH=src "$PY" -m pytest -q tests/test_simulate.py tests/sinks tests/mcp

echo "==> [4/7] CLI help + studio-report smoke"
PYTHONPATH=src "$PY" -m superdeterminism --help >/dev/null
PYTHONPATH=src "$PY" -m superdeterminism studio-report examples/advisor_flip_to_det.json \
  --out /tmp/unagent_studio_validate.json --n-min 1

echo "==> [5/7] orchestrator studio-report smoke"
PYTHONPATH=src "$PY" -m superdeterminism studio-report demos/e2e-orchestrator/traces.json \
  --out /tmp/unagent_orchestrator_validate.json --n-min 30

echo "==> [6/7] UI unit tests + build"
if [[ -d ui ]]; then
  (cd ui && npm ci --prefer-offline --no-audit --no-fund && npm test && npm run build)
else
  echo "skip: no ui/"
fi

echo "==> [7/7] playwright smoke (optional)"
if [[ -d ui ]] && command -v npx >/dev/null 2>&1 && [[ "${RUN_PLAYWRIGHT:-0}" == "1" ]]; then
  (cd ui && npx playwright test)
else
  echo "skip: set RUN_PLAYWRIGHT=1 to enable"
fi

echo "validate.sh OK"
