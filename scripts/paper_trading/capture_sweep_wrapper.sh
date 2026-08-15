#!/bin/bash
# capture_sweep_wrapper.sh
# HermesForge US-107 — Wrapper for STR-Q intraday sweep capture
# Runs capture + exit monitor, outputs JSON for cron consumption

cd /root/HermesForge

# Run sweep capture (crypto only when stocks closed, both when stocks open)
python3 scripts/paper_trading/capture_sweep_signals.py 2>&1