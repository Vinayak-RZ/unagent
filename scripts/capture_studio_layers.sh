#!/usr/bin/env bash
# Capture Studio layer PNGs (manual / computer-use helper).
# ponytail: documents URLs; full headless capture is P1 (Playwright).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/docs/assets/e2e-orchestrator"
REPORT_URL="http://127.0.0.1:5173/?report=/e2e_orchestrator_studio_report.json"

echo "Start Studio: cd ui && npm run dev"
echo "Open: ${REPORT_URL}"
echo "Capture to: ${OUT}/"
echo "  layer_L0_orchestrator.png       — L0 tab, root graph"
echo "  layer_L1_agents.png             — L1 tab"
echo "  layer_L1_research_agent_tools.png — L2 tab or drill research_agent"
echo "  layer_lens_controls.png         — L0 with lens visible"
echo "  studio_simulation_playback.png  — Cinematic + Play mid-run"
echo "  studio_simulation_cinematic.mp4 — screen recording of full walkthrough"
