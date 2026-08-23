#!/bin/bash
# Wrapper for cron: runs capture_signals.py (EPIC-010 paper trading, live +
# watch strategies only). 7 days/week — crypto scans 7d, stocks on weekdays.
# Silent by default (no_agent watchdog pattern).
#
# 2026-08-23: cropped to 6 strategies (live + watch only, killed dropped).
# 2026-07-27 update: fetch fresh crypto data before scanning (crypto trades
# 24/7, cache max age is 1 day). Stock data is fetched separately by the
# daily_publish pipeline at 14:45 UTC (5 min before this runs at 14:50).
set -euo pipefail
cd /root/HermesForge

# Load environment variables (API keys for sweep detection, regime filter, etc.)
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//') 2>/dev/null || true

# Refresh crypto data (Hyperliquid public API, free, no auth)
python3 scripts/paper_trading/fetch_crypto_data.py 2>&1

DOW=$(date +%u)  # 1=Mon ... 7=Sun
EXTRA_ARGS=""

# Weekdays (Mon-Fri): stock + crypto paper trading
# Weekend (Sat-Sun): crypto-only (stocks market is closed)
if [ "$DOW" -ge 6 ]; then
    # Refresh stock data for context but scan crypto only
    python3 scripts/validation/fetch_data.py 2>&1 || true
    EXTRA_ARGS="--crypto-only"
else
    # Refresh stock data and scan both
    python3 scripts/validation/fetch_data.py 2>&1
fi

# Run paper trading capture (regime-aware, live+watch strategies only)
OUTPUT="$(python3 scripts/paper_trading/capture_signals.py $EXTRA_ARGS 2>&1)"

OPENED=$(echo "$OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
m = re.search(r'--- JSON ---\s*\n(.*)', text, re.DOTALL)
if not m:
    print(-1)
else:
    try:
        data = json.loads(m.group(1))
        print(data.get('opened', -1))
    except Exception:
        print(-1)
")

ERRORS=$(echo "$OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
m = re.search(r'--- JSON ---\s*\n(.*)', text, re.DOTALL)
if not m:
    print(-1)
else:
    try:
        data = json.loads(m.group(1))
        print(data.get('errors', -1))
    except Exception:
        print(-1)
")

if [ "$OPENED" != "0" ] || [ "$ERRORS" != "0" ]; then
    echo "$OUTPUT"
fi
