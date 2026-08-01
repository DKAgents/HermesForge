---
type: regime
regime_type: high-volatility
description: "Elevated volatility with large daily ranges, VIX > 25 or ATR > 2x average"
indicators: [VIX > 25, ATR > 2x 50-day average, wide Bollinger Bands]
applicable_strategies: [STR-M, STR-N]
tags: [regime, high-volatility]
---

# Regime: High Volatility

Elevated market volatility with large daily price ranges. Risk management becomes paramount — position sizing must account for wider stops.

## Strategies That Work Here

None currently pass. Two strategies tested and killed in W32:

- [[STR-20260726-selling-climax-reversal|STR-M Selling Climax]] — killed, -1.000 avg R. Selling climax is a market-level pattern, not per-stock.
- [[STR-20260726-outside-day-key-reversal|STR-N Outside Day]] — killed, -0.037 avg R overall but +0.332 in period3_current. Regime-dependent edge, future research path.

## Key Indicators

- VIX > 25
- ATR > 2x its 50-day average
- Bollinger Bands abnormally wide
- Large true range bars

## Research Opportunity

High-volatility regime remains the hardest to crack. Two reversal-based strategies (STR-M, STR-N) both failed overall, though STR-N shows a promising regime-dependent edge in 2024+. Future approaches:
- Volatility-breakout (not reversal) in high-vol — different from STR-F (which was low-vol squeeze breakout)
- Mean-reversion with wider stops and longer hold time
- Regime-gated version of STR-N that only activates in post-2024 conditions
- Selling climax at the index/ETF level (SPY/QQQ) rather than per-stock

## Related
- [[REGIME-low-volatility]]
- [[RISK_RULES]]
- [[STRATEGIES-MOC]]
