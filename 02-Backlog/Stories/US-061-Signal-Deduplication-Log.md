---
id: US-061
epic: EPIC-009
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [discord, deduplication, signals, logging]
depends-on: US-060
---

# US-061: Signal Deduplication Log

## Story
As a signal publisher, I need a deduplication mechanism that prevents the same setup from being posted to Discord repeatedly, so that channels are not flooded with repeated alerts for ongoing setups.

## Acceptance Criteria
- [ ] Deduplication log at `scripts/discord/published_signals.csv` with schema:
  `signal_id, strategy_id, ticker, entry_date, published_at, channel`
- [ ] Signal ID defined as: `{strategy_id}_{ticker}_{entry_date}` (e.g. `STR-B_NVDA_2026-07-20`)
- [ ] Function `is_duplicate(signal_id, lookback_days=5)` in `scripts/discord/dedup.py`:
  - Returns True if signal_id was published in the last `lookback_days` trading days
  - Returns False if not found or older than lookback window
- [ ] Function `record_published(signal_id, strategy_id, ticker, entry_date, channel)` appends to CSV
- [ ] Publisher pipeline (US-060) calls `is_duplicate()` before posting; skips if True
- [ ] On skip: logs reason to stdout (`SKIP: {signal_id} already published {N} days ago`)
- [ ] Lookback window configurable (default 5 trading days)

## Definition of Done
- dedup.py and published_signals.csv created
- is_duplicate() and record_published() tested with unit test
- Committed to main
