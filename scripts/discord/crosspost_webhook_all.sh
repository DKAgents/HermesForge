#!/bin/bash
# crosspost_webhook_all.sh — canonical webhook cross-post forwarder.
#
# Forwards ALL non-cross-posted bot messages in the last 24h, oldest-first,
# from every allow-listed channel (8 channels, all enabled), validating each
# against the template gate (US-148) and re-uploading any chart attachment
# (fixes B1 chart-drop and B2 multi-part loss).
#
# The heavy lifting — forward-all, template validation, atomic-write +
# regression guard (US-123/125/126/131), dedup state, and chart re-upload —
# all live in the single Publisher-owned module
# publisher_templates.forward_all_channels().  This script is a thin wrapper so
# the cron can invoke it, and is intentionally IDENTICAL to the repo copy at
# scripts/discord/crosspost_webhook_all.sh (a single canonical script, no
# drifted duplicates).
#
# Usage: crosspost_webhook_all.sh [--dry-run]
set -euo pipefail

# Source secrets (DISCORD_BOT_TOKEN + CROSSPOST_WEBHOOK_* channel webhooks).
set -a; source /root/.hermes/.env; set +a

REPO_DISCORD="/root/HermesForge/scripts/discord"

# US-193: single source-of-truth interpreter (never bare python3 — the tools
# python has no third-party deps). publisher_templates needs pandas/matplotlib.
PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"

DRY_RUN=""
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
fi

"$PYTHONBIN" "${REPO_DISCORD}/publisher_templates.py" --forward-all ${DRY_RUN}
exit $?