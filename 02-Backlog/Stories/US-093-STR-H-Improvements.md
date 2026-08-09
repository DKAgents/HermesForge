---
id: US-093
epic: EPIC-002
type: story
status: backlog
created: 2026-08-07
points: 5
tags: [backlog, story]
---

# US-093: STR-H Hype Strategy Improvements

## Story
**As the** research system,
**I want** to improve the STR-H Hype strategy with social sentiment data, 4h timeframe testing, and a survivorship-bias-free universe,
**So that** the marginal OOS edge can be properly evaluated or rejected.

## Acceptance Criteria
- [ ] Integrate free-tier social data (LunarCrush free API, Santiment, or Reddit mention scraper) to filter volume spikes by actual sentiment
- [ ] Fetch 4h crypto bars from Hyperliquid and re-run walk-forward on 4h timeframe
- [ ] Include currently-delisted coins in backtest universe (manual price history from CoinGecko) to remove survivorship bias
- [ ] Compare results with/without social filter to determine if social data adds alpha beyond pure price/volume momentum

## Notes / Context
> STR-H currently MARGINAL OOS (mean R +0.142, win rate 32.8%, max DD 10.88R). Lottery-ticket distribution. If social filter adds no alpha, drop it and trade pure ignition pattern.

## Dependencies
- Blocks: None
- Blocked by: Free social data source availability

## Definition of Done
- [ ] Code/config implemented
- [ ] Tests passing (paper mode verified)
- [ ] Risk Guardian reviewed (if applicable)
- [ ] Documented in vault
- [ ] ADR created (if architectural decision)
