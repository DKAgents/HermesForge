#!/usr/bin/env bash
# digest.sh — cron wrapper for the confidence-digest renderer (US-161).
# Pins the dependency-complete venv Python explicitly (US-163 step 1).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONBIN="$("$DIR/resolve_python.sh")"
exec "$PYTHONBIN" "$DIR/digest.py" "$@"