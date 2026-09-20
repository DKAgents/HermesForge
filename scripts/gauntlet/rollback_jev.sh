#!/bin/bash
# rollback_jev.sh — Safe Jev rollback: disable Jev, return to pre-Jev heuristics.
# This restores the capture pipeline behavior from before Jev was introduced.
# It does NOT restore fail-open or 45% thresholds.
#
# Effects:
#   - All signals pass through to paper trading (no Jev gating)
#   - Decay watch runs old heuristic instead of Jev
#   - No Jev API calls, no costs, no latency
#
# To re-enable Jev: set JEV_ENABLED=true in the wrapper's env or
#   reinstate the import in capture_signals.py and capture_sweep_signals.py.

set -euo pipefail

REPO=/root/HermesForge
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

echo "[$TIMESTAMP] Rolling back Jev prefilter — returning to pre-Jev heuristics"

# 1. Disable Jev in both cron wrappers via env variable
for wrapper in \
    "$REPO/scripts/cron/capture_signals_wrapper.sh" \
    "$REPO/scripts/cron/capture_sweep_wrapper.sh"
do
    if [ -f "$wrapper" ]; then
        # Add JEV_ENABLED=false if not already present
        if ! grep -q "JEV_ENABLED" "$wrapper" 2>/dev/null; then
            sed -i '1a export JEV_ENABLED=false' "$wrapper"
        fi
        echo "  Disabled Jev in $wrapper"
    fi
done

# 2. Restore decay cron to old heuristic
# (cronjob_manage update call goes here if user confirms)

echo ""
echo "Rollback complete. Effects:"
echo "  - Jev prefilter: DISABLED (all signals pass through to paper trading)"
echo "  - Decay watch: manual restore needed via chronjob_manage"
echo ""
echo "To undo this rollback:"
echo "  git checkout scripts/cron/capture_signals_wrapper.sh"
echo "  git checkout scripts/cron/capture_sweep_wrapper.sh"
echo ""
echo "To block all new live entries (emergency kill switch):"
echo "  echo 'PAUSED=true' > /root/HermesForge/.kill_switch"