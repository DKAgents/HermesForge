#!/bin/bash
# post_weekly_funnel.sh — US-190 weekly cron wrapper.
# Runs the consolidated per-gate funnel generator and posts it to the
# Strategy Status channel. Uses the single source-of-truth interpreter
# (resolve_python.sh), never bare python3.
set -euo pipefail

# Source secrets (DISCORD_BOT_TOKEN + channel IDs).
set -a; source /root/.hermes/.env; set +a

PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"
"$PYTHONBIN" /root/HermesForge/scripts/discord/post_weekly_funnel.py "$@"