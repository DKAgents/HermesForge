#!/bin/bash
# vrp_paper_forward_wrapper.sh — HermesForge US-181 cron wrapper for the daily
# short-vol / VRP paper-forward accumulation runner (HYPOTHESIS, not promoted).
#
# Runs scripts/gauntlet/vrp_paper_forward.py via the dependency-complete
# interpreter resolved by resolve_python.sh (Rule 1d — NEVER bare python3;
# US-163).
set -euo pipefail
cd /root/HermesForge
PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"   # Rule 1d

# Load environment variables (consistent with sibling wrappers).
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//') 2>/dev/null || true

"$PYTHONBIN" scripts/gauntlet/vrp_paper_forward.py "$@"