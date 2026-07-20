---
id: US-069
epic: EPIC-010
type: story
status: done
created: 2026-07-20
points: 5
tags: [paper-trading, crypto, data-source]
depends-on: US-065
---

# US-069: Crypto Data Source Integration (BTC/ETH/SOL)

## Story
As a paper trading system, I need OHLCV data for the approved crypto universe (BTC, ETH, SOL) so that crypto signals can be scanned and outcomes tracked the same way as stocks.

## Acceptance Criteria
- [ ] Script `scripts/paper_trading/fetch_crypto_data.py` that fetches daily OHLCV for BTC, ETH, SOL
  - Recommended source: Hyperliquid's public market-data REST endpoint (no auth required, and reused later for EPIC-011 — avoids introducing a second crypto data vendor)
  - Fallback if Hyperliquid public data proves insufficient for backtest-depth history: yfinance crypto tickers (`BTC-USD`, `ETH-USD`, `SOL-USD`) — flag this as a decision point in the story, not pre-decided
- [ ] Caches to `~/.hermes/market_data/crypto/{SYMBOL}.parquet`, same column schema as stock parquet files (open, high, low, close, volume) for scanner compatibility
- [ ] Adapts existing scanners (A, B, D) to run against crypto data — confirm which strategies make sense for 24/7 markets (no weekly/session gaps) and flag any strategy-specific adjustments needed (e.g. Strategy A's weekly-gate logic assumes stock market weekly bars — crypto trades 7 days/week, so "weekly" bar definition needs an explicit decision)
- [ ] Smoke test: fetch and cache BTC data, run Strategy B scanner against it, confirm no crash (signal count may be zero — that's fine for a smoke test)

## Definition of Done
- Crypto data cached and scanner-compatible for BTC/ETH/SOL
- At least one scanner runs against crypto data without error
- Design decision on weekly-bar definition for crypto documented (even if deferred)
- Committed to main
