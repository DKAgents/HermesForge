#!/bin/bash
# capture_sweep_wrapper.sh
# HermesForge US-107 — Wrapper for STR-Q intraday sweep capture
# Runs sweep capture, outputs JSON for cron consumption

cd /root/HermesForge

# Load environment variables
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//' 2>/dev/null) 2>/dev/null || true

# Run sweep capture (crypto only when stocks closed, both when stocks open)
python3 scripts/paper_trading/capture_sweep_signals.py 2>&1