#!/usr/bin/env bash
# Connection Discovery wrapper with 24h change guard
# Exits silently (exit 0, no output) if vault has no .md changes in last 24h
# Otherwise runs discover_connections.py and passes through output

set -euo pipefail

VAULT_ROOT="/root/HermesForge"
SCRIPT="$VAULT_ROOT/scripts/discover_connections.py"

# Count .md files modified in last 24h (exclude .obsidian/.git)
CHANGED=$(find "$VAULT_ROOT" -name "*.md" -mmin -1440 \
  -not -path "*/.obsidian/*" \
  -not -path "*/.git/*" \
  -not -path "*/__pycache__/*" \
  2>/dev/null | wc -l)

if [ "$CHANGED" -eq 0 ]; then
  # No changes — silent exit
  exit 0
fi

echo "=== Connection Discovery: $CHANGED vault files changed in last 24h ==="
python3 "$SCRIPT"
