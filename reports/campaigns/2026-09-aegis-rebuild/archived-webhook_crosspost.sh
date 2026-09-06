#!/bin/bash
# webhook_crosspost.sh - Crosspost the latest message from a source channel
# to the follower server via webhook (replaces native announcement crosspost).
#
# Usage: webhook_crosspost.sh <channel_id>
# Silent on success (no output). Prints errors on failure (watchdog pattern).
# Requires: DISCORD_BOT_TOKEN and CROSSPOST_WEBHOOK_{channel_id} in /root/.hermes/.env

set -euo pipefail

CHANNEL_ID="${1:-1532020053548208328}"  # default: daily market briefing

set -a; source /root/.hermes/.env; set +a

# Get the webhook URL for this channel
WEBHOOK_ENV_VAR="CROSSPOST_WEBHOOK_${CHANNEL_ID}"
WEBHOOK_URL="${!WEBHOOK_ENV_VAR:-}"

if [ -z "$WEBHOOK_URL" ]; then
    echo "ERROR: No webhook configured for channel $CHANNEL_ID (env var $WEBHOOK_ENV_VAR not set)"
    exit 1
fi

# Fetch the latest message from the source channel
LATEST=$(curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages?limit=1")

# Extract message content and embeds
MSG_JSON=$(echo "$LATEST" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not isinstance(data, list) or len(data) == 0:
    print(json.dumps({'error': 'no messages'}))
    sys.exit(0)
msg = data[0]
payload = {}
if msg.get('content'):
    payload['content'] = msg['content']
if msg.get('embeds'):
    payload['embeds'] = msg['embeds']
payload['username'] = 'HermesForge Bot'
if not payload.get('content') and not payload.get('embeds'):
    print(json.dumps({'error': 'empty message'}))
else:
    print(json.dumps(payload))
" 2>/dev/null)

if echo "$MSG_JSON" | grep -q '"error"'; then
    echo "ERROR: Could not extract message from channel $CHANNEL_ID"
    echo "$MSG_JSON"
    exit 1
fi

# Post via webhook to the follower channel
RESULT=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$MSG_JSON" \
  -w "\nHTTP:%{http_code}" \
  "${WEBHOOK_URL}?wait=true")

HTTP_CODE=$(echo "$RESULT" | grep -o 'HTTP:[0-9]*' | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ]; then
    # Success - stay silent
    exit 0
else
    echo "ERROR: Webhook crosspost failed (HTTP $HTTP_CODE)"
    echo "Channel: $CHANNEL_ID"
    echo "$RESULT" | head -5
    exit 1
fi
