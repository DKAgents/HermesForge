#!/bin/bash
# crosspost_webhook_all.sh — Webhook crosspost all recent messages in configured channels
#
# Uses CROSSPOST_WEBHOOK_{CHANNEL_ID} env vars to push a copy of the latest
# message from each source channel to the corresponding follower channel.
# Only crossposts messages posted by the bot in the last hour.
# Silent when nothing to do.
#
# Usage: crosspost_webhook_all.sh [--dry-run]

set -euo pipefail
set -a; source /root/.hermes/.env; set +a

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    shift
fi

# All 8 source channels that should be crossposted
CHANNELS=(
    1528555538848153640  # stock-setups
    1528555885310513213  # crypto-setups
    1532020053548208328  # daily-market-briefing
    1533332485641998386  # strategy-status
    1534834809451450409  # strategy-research
    1537225420120793088  # paper-trading
    1540951134200402071  # day-trade-crypto
    1540951208028803142  # day-trade-stocks
)

CROSSPOSTED=0
SKIPPED=0

TOKEN="${DISCORD_BOT_TOKEN:-}"

if [ -z "$TOKEN" ]; then
    echo "ERROR: DISCORD_BOT_TOKEN not set"
    exit 1
fi

for CHANNEL_ID in "${CHANNELS[@]}"; do
    WEBHOOK_VAR="CROSSPOST_WEBHOOK_${CHANNEL_ID}"
    WEBHOOK_URL="${!WEBHOOK_VAR:-}"
    
    if [ -z "$WEBHOOK_URL" ]; then
        continue  # No webhook configured for this channel — skip silently
    fi
    
    # Fetch the latest bot messages from the source channel (last 24h)
    ONE_DAY_AGO=$(date -u -d '24 hours ago' +%s 2>/dev/null || python3 -c "import time; print(int(time.time() - 86400))")
    export ONE_DAY_AGO
    
    MESSAGES=$(curl -s -H "Authorization: Bot ${TOKEN}" \
        "https://discord.com/api/v10/channels/${CHANNEL_ID}/messages?limit=5" 2>/dev/null)
    
    if [ -z "$MESSAGES" ]; then
        continue
    fi
    
    # Find the most recent non-empty bot message within the last 24h
    # that hasn't been crossposted yet
    LATEST_MSG=$(echo "$MESSAGES" | python3 -c "
import json, sys, os
data = json.load(sys.stdin)
if not isinstance(data, list):
    sys.exit(0)
cutoff = int(os.environ.get('ONE_DAY_AGO', 0))
for msg in data:
    ts = int(msg.get('id', '0')[:10]) if msg.get('id') else 0
    # Snowflake ID auto-converts to timestamp: (id >> 22) + 1420070400000
    timestamp = (int(msg['id']) >> 22) + 1420070400000
    timestamp_s = int(timestamp / 1000)
    if timestamp_s < cutoff:
        continue
    flags = msg.get('flags', 0)
    already = bool(flags & 1)
    content = msg.get('content', '').strip() or (msg.get('embeds') and msg['embeds'])
    if content and not already:
        print(msg['id'])
        break
" ONE_DAY_AGO="$ONE_DAY_AGO" 2>/dev/null)
    
    if [ -z "$LATEST_MSG" ]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] Would crosspost msg $LATEST_MSG from $CHANNEL_ID via webhook"
        CROSSPOSTED=$((CROSSPOSTED + 1))
        continue
    fi
    
    # Post to webhook: re-fetch the message content and forward it
    MSG_CONTENT=$(echo "$MESSAGES" | python3 -c "
import json, sys
data = json.load(sys.stdin)
target = '$LATEST_MSG'
for msg in data:
    if msg.get('id') == target:
        content = msg.get('content', '')
        embeds = msg.get('embeds', [])
        attachments = msg.get('attachments', [])
        result = {'content': content}
        if embeds:
            result['embeds'] = embeds
        print(json.dumps(result))
        break
" 2>/dev/null)
    
    if [ -z "$MSG_CONTENT" ] || [ "$MSG_CONTENT" = "{}" ]; then
        continue
    fi
    
    # Post via webhook
    RESULT=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$MSG_CONTENT" \
        --max-time 10 \
        "${WEBHOOK_URL}?wait=true" 2>/dev/null)
    
    if echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null | grep -q .; then
        CROSSPOSTED=$((CROSSPOSTED + 1))
    fi
    
    sleep 0.5  # Rate limit buffer
done

if [ "$CROSSPOSTED" -gt 0 ] || [ "$DRY_RUN" = true ]; then
    echo "Crosspost: $CROSSPOSTED messages, $SKIPPED skipped"
fi