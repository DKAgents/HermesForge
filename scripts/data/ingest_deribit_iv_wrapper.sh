#!/bin/bash
# ingest_deribit_iv_wrapper.sh — HermesForge US-187 cron wrapper for hourly
# Deribit DVOL + ATM IV term-structure ingestion.
#
# Runs scripts/data/ingest_deribit_iv.py via the dependency-complete interpreter
# resolved by resolve_python.sh (Rule 1d — NEVER bare python3; US-163).
set -euo pipefail
cd /root/HermesForge
PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"   # Rule 1d

# Load environment variables (harmless here, but consistent with siblings).
source /root/.hermes/.env 2>/dev/null
export $(grep -E '^[A-Z_]+=' /root/.hermes/.env | sed 's/=.*//') 2>/dev/null || true

"$PYTHONBIN" scripts/data/ingest_deribit_iv.py "$@"