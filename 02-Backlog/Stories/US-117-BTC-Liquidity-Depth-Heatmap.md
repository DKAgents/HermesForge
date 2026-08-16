---
id: US-117
type: user-story
epic: EPIC-009
status: in-progress
priority: medium
effort: M
created: 2026-08-16
updated: 2026-08-16
assigned_to: agent
tags: [backlog, story, crypto, liquidity, heatmap, OI, bitcoin]
---

# US-117: BTC Liquidity Depth Heatmap

## Story
**As a** trading researcher,
**I want** a heatmap showing where pools of liquidity sit by price level for BTC,
**So that** I can identify support/resistance from orderbook depth and OI concentration.

## Context
User requested a BTC OI heatmap to analyze where liquidity pools sit. Research found:
- Binance: geo-blocked from VPS (403)
- Bybit: geo-blocked (403)
- Coinglass: needs API key (free tier 10k calls/month, V4 endpoints)
- OKX: works — 100-level L2 orderbook + total OI
- Hyperliquid: works — 20-level L2 book + total OI + funding

No free API provides true OI-by-price-level (Coinglass premium). Built liquidity depth heatmap from orderbook aggregation instead.

## Acceptance Criteria
- [x] Fetch L2 orderbook from OKX (100 levels) and Hyperliquid (20 levels)
- [x] Aggregate bid/ask depth into price bins
- [x] Generate visual PNG heatmap with color intensity by liquidity concentration
- [x] Generate text summary with top bid/ask walls
- [x] Show total OI from both exchanges
- [ ] Set up recurring cron (on-demand for now)
- [ ] Explore Coinglass API key for wider OI-by-price coverage
- [ ] Integrate into Discord posting pipeline

## Implementation
- `scripts/data/liquidity_heatmap.py` — fetches, aggregates, generates PNG + text summary
- Default bin size: $5 (tuned for BTC's narrow orderbook range)
- Output: `~/.hermes/market_data/heatmaps/BTC_liquidity_heatmap.png`

## Limitations
- Exchange orderbooks only expose ~$30-50 price range around mid price
- This shows immediate liquidity walls (useful for entry/exit timing)
- Does NOT show OI distribution across a wide price range (would need Coinglass)
- OI/Liquidity ratio of ~1000x shows how leveraged the market is relative to resting liquidity
