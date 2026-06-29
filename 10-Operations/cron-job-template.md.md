# Cron Job Template

Use this pattern when creating new cron jobs that Hermes or other automation will run.

## Standard Script Header

```bash
#!/bin/bash
# =====================================================
# HermesForge Cron Job Template
# =====================================================

set -euo pipefail

# Load SSH key if needed
eval $(keychain --eval --agents ssh --quiet id_ed25519_hermesforge)

# Configuration
LOG_DIR="$HOME/logs/hermes"
mkdir -p "$LOG_DIR"
LOG_FILE="$$   LOG_DIR/   $$(basename "$0")-$(date +%Y%m%d).log"

exec >> "$LOG_FILE" 2>&1

echo "=== $(date) - Starting $(basename "$0") ==="

# === Your script logic goes here ===

echo "=== $(date) - Finished $(basename "$0") ==="