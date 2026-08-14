---
type: user-story
status: done
epic: EPIC-011
priority: high
created: 2026-08-14
completed: 2026-08-14
---

# US-103: Free Data Sources + Universal Regime Filter

## Story
As a trading researcher, I need additional market data sources (Fear & Greed, funding rates, macro indicators) combined into a universal regime filter that tags every trade with regime context for later analysis.

## Acceptance Criteria
- [x] Crypto Fear & Greed Index fetcher (alternative.me, free, no key)
- [x] Hyperliquid funding rates + open interest fetcher
- [x] Macro data fetcher (DXY, Treasury yields, VIX via yfinance)
- [x] Universal regime filter combining all sources
- [x] Regime tags applied to every new trade in capture_signals.py
- [x] Daily market intelligence cron includes regime assessment
- [x] All fetchers tested with live data

## Implementation
- `scripts/data/fetch_fear_greed.py` — 3113 days of F&G history
- `scripts/data/fetch_hyperliquid_metrics.py` — Funding + OI for 10 coins
- `scripts/data/fetch_macro.py` — DXY, TNX, FVX, IRX, VIX (2 years)
- `scripts/data/regime_filter.py` — Combined regime assessment + tag_signal()
- `scripts/paper_trading/capture_signals.py` — Regime tagging on every trade
- Daily intelligence cron updated to include regime report

## Data Sources Summary
| Source | Data | Cost | Status |
|--------|------|------|--------|
| alternative.me | Crypto Fear & Greed | Free | ✅ Online |
| Hyperliquid API | Funding rates, OI | Free | ✅ Online |
| yfinance | DXY, Treasury yields, VIX | Free | ✅ Online |
| LunarCrush | Social sentiment | Free (500/day) | ⏸️ Needs API key |
