#!/bin/bash
# trade_monitor_triage.sh — US-156
# Wrapper: runs trade monitor, pipes through JEV triage.
# Only outputs full report on WARN/CRITICAL; silent on OK.
# Eliminates ~700 T3 agent calls/month when nothing happens.

set -euo pipefail
cd /root/HermesForge

# Run trade monitor
MONITOR_OUT=$(python3 scripts/paper_trading/trade_monitor.py 2>&1) || {
    echo "🔴 Trade Monitor crashed"
    echo "$MONITOR_OUT"
    exit 0
}

# Pipe through JEV triage
TRIAGE_RESULT=$(echo "$MONITOR_OUT" | python3 scripts/monitoring/jev_cron_triage.py --cron-name "trade-monitor-60m" 2>&1)
TRIAGE_EXIT=$?

case $TRIAGE_EXIT in
    0)  # OK — nothing happened, save tokens
        exit 0
        ;;
    1)  # WARN — output relevant lines
        echo "⚠️ Trade Monitor: attention needed"
        echo "$MONITOR_OUT" | grep -E "STOP|TARGET|TIME|ERROR|ENTRY|Still open|Alerts posted" || echo "$MONITOR_OUT"
        exit 0
        ;;
    2)  # CRITICAL — output full report
        echo "🔴 Trade Monitor: critical — full output follows"
        echo "$MONITOR_OUT"
        exit 0
        ;;
esac