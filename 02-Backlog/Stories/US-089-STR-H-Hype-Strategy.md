---
id: US-089
epic: EPIC-002
type: story
status: done
created: 2026-08-07
points: 5
tags: [backlog, story]
---

# US-089: STR-H Hype Strategy

## Story
**As a** research system,
**I want** a hype/momentum-ignition strategy tested on crypto markets,
**So that** I can evaluate whether volume-acceleration proxies can capture social-media-driven price moves.

## Acceptance Criteria
- [x] `hype_strategy.py` built (crypto-only)
- [x] Entry: volume spike 3x 7-bar baseline + close in top 25% + 2x 20-bar volume expansion
- [x] 50/50 scale-in: ignition entry + pullback to 8-EMA
- [x] Swing-low stop loss
- [x] Trailing exit (8-EMA), hard exit (21-EMA), 3-bar time stop
- [x] BTC>SMA50 regime filter applied
- [x] 0.5% risk per trade
- [x] Walk-forward tested: 215 trades, mean R +0.130, but 32.8% OOS win rate (MARGINAL)

## Notes / Context
> Commits 592ab75 and 6e254ce. VERDICT: MARGINAL OOS — not deployable at size. Lottery-ticket distribution (few big winners, many small losers). Social data is proxied by volume (honest limitation — true social sentiment data not available). Survivorship bias acute for hype strategy since many hyped coins delist.

## Dependencies
- Blocks: None
- Blocked by: None

## Definition of Done
- [x] Code/config implemented
- [x] Tests passing (paper mode verified)
- [x] Risk Guardian reviewed (if applicable)
- [x] Documented in vault
- [x] ADR created (if architectural decision)
