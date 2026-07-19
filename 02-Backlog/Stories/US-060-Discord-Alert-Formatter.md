---
id: US-060
epic: EPIC-009
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [discord, alerts, formatting, publisher]
depends-on: US-059
---

# US-060: Discord Alert Formatter and Publisher

## Story
As a signal publisher, I need a module that formats a signal as a rich Discord message and posts it (with chart image) to the correct channel, so that users receive clear, actionable alerts.

## Acceptance Criteria
- [ ] Module `scripts/discord/alert_publisher.py` with function `publish_signal(signal_dict, chart_path)`
- [ ] Reads target channel from signal's strategy frontmatter (`publish_channel` field)
- [ ] Message format (Discord embed or plain text with structure):

```
📊 **{STRATEGY_NAME} v{VERSION}** — {CONFIDENCE} confidence

**{TICKER}** · {DIRECTION} · Daily

📍 Entry:  ${ENTRY}
🛑 Stop:   ${STOP}  ({STOP_PCT}% risk)
🎯 Target: ${TARGET}  (R:R {RR}:1)
💰 Size:   {RISK_PCT}% account risk → {EXAMPLE_SHARES} shares @ $100k

**Signal:** {KEY_CONDITIONS_1LINE}
**Regime:** {SUBPERIOD_LABEL}

_Posted: {DATETIME} UTC_
```

- [ ] Chart PNG attached as image in the same message
- [ ] Uses Hermes send_message tool or direct Discord webhook (whichever is simpler from VPS cron context)
- [ ] Channel mapping:
  - `publish_channel: stocks` → Discord channel #stock-setups
  - `publish_channel: crypto` → Discord channel #crypto-setups
- [ ] Channel IDs stored in `scripts/discord/config.py` (not hardcoded in publisher)
- [ ] Dry-run mode: `publish_signal(..., dry_run=True)` prints formatted message without posting
- [ ] Smoke test: dry-run with synthetic signal, verify output format

## Definition of Done
- alert_publisher.py runnable standalone with dry-run
- Channel config documented
- Committed to main
