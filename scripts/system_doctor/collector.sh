#!/usr/bin/env bash
# collector.sh — cron wrapper for the system-doctor mechanical collector (US-158).
# Pins the dependency-complete venv Python via resolve_python.sh (US-163 step 1):
# NEVER bare `python3` (resolves to bare tools Python with no third-party deps).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONBIN="$("$DIR/resolve_python.sh")"
exec "$PYTHONBIN" "$DIR/collector.py" "$@"