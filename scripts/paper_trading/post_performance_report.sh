#!/bin/bash
# HermesForge Paper Trading Performance Report — publisher pipeline
# Wraps embed_publisher.publish_performance_report() for cron.
set -euo pipefail
cd /root/HermesForge

# Source secrets
source /root/.hermes/.env 2>/dev/null

python3 -c "
from discord.embed_publisher import publish_performance_report
result = publish_performance_report(crosspost=True)
status = result.get('status', 'error')
if status == 'ok':
    msg_id = result.get('message_id', '?')
    ch_id = result.get('channel_id', '?')
    print(f'Report posted: msg_id={msg_id} channel={ch_id} crosspost=True')
else:
    error = result.get('error', 'Unknown')
    print(f'Failed: {error}')
    exit(1)
"