#!/bin/bash
# ingest_lunarcrush_wrapper.sh — HermesForge US-200 cron wrapper for the daily
# LunarCrush sentiment ingest (free/limited tier, labeled source=lunarcrush).
#
# Runs scripts/data/fetch_lunarcrush.py (--crypto-only --topics-only) via the
# dependency-complete interpreter resolved by resolve_python.sh (Rule 1d —
# NEVER bare python3; US-163). Each daily snapshot is persisted to
# ~/.hermes/market_data/lunarcrush/{crypto|topics}_YYYY-MM-DD.parquet with a
# `source=lunarcrush` column.
set -euo pipefail
cd /root/HermesForge
PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"   # Rule 1d

# Load environment variables (LUNARCRUSH_API_KEY among them).
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//') 2>/dev/null || true

"$PYTHONBIN" scripts/data/fetch_lunarcrush.py --crypto-only --topics-only "$@"