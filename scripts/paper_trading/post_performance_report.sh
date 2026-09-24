#!/bin/bash
# Wrapper for cron: runs performance_report.py and posts to paper-trading channel.
# Posts to source server paper-trading (#1537225420120793088) via Discord API.
set -euo pipefail
cd /root/HermesForge

# Run the report
REPORT=$(python3 scripts/paper_trading/performance_report.py 2>&1)

if [ -z "$REPORT" ]; then
    echo "Report empty — nothing to post"
    exit 0
fi

# Post to paper-trading channel via Discord API
source /root/.hermes/.env 2>/dev/null
TOKEN="${DISCORD_BOT_TOKEN:-}"

if [ -z "$TOKEN" ]; then
    echo "ERROR: DISCORD_BOT_TOKEN not set"
    exit 1
fi

# Discord has a 2000 char limit per message — split if needed
echo "$REPORT" | python3 -c "
import sys, json, urllib.request, os

content = sys.stdin.read().strip()
if not content:
    sys.exit(0)

token = os.environ.get('DISCORD_BOT_TOKEN', '$TOKEN')
channel_id = '1537225420120793088'  # paper-trading

# Split into 2000-char chunks
chunks = []
while len(content) > 1900:
    split_at = content.rfind('\n', 0, 1900)
    if split_at == -1:
        split_at = 1900
    chunks.append(content[:split_at])
    content = content[split_at:].lstrip()
chunks.append(content)

for chunk in chunks:
    payload = json.dumps({'content': chunk}).encode()
    req = urllib.request.Request(
        f'https://discord.com/api/v10/channels/{channel_id}/messages',
        data=payload,
        headers={
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            pass
    except Exception as e:
        print(f'Post error: {e}', file=sys.stderr)
"

echo "Report posted to paper-trading channel"