---
type: regime
regime_type: trending
description: "Sustained directional price movement with higher highs/lower lows"
indicators: [ADX > 25, price above/below 200 SMA, MACD histogram expanding]
applicable_strategies: [STR-I, STR-B, STR-A, STR-H]
tags: [regime, trending]
---

# Regime: Trending

Sustained directional price movement where trend-following and pullback strategies tend to outperform. Characterized by expanding MACD histogram, price persistently above (bull) or below (bear) the 200-day SMA, and ADX above 25.

## Strategies That Work Here

- [[STR-20260728-adaptive-trend|STR-I AdaptiveTrend]] — momentum entry with ATR trailing stop
- [[STR-20260719-macd-histogram-divergence-weekly-assessment|STR-B MACD Divergence]] — divergence with weekly trend gate
- [[STR-20260719-ma-pullback-fibonacci-entry|STR-A MA Pullback]] — fibonacci entry at pullback to 50 MA

## Strategies That Fail Here

- [[STR-20260726-rsi-mean-reversion-entry|STR-E RSI Mean-Reversion]] — killed, mean-reversion fails in trends
- [[STR-20260726-eufearia-cci-reversal|STR-J EUFEARIA CCI]] — underperforms in trending phases

## Key Indicators

- ADX(14) > 25
- Price above/below 200-day SMA
- MACD histogram expanding
- Higher highs / lower lows pattern

## Active Strategy Mapping (Regime-Aware Pipeline)

Strategies activated when this regime is detected:
- [[STR-20260719-macd-histogram-divergence-weekly-assessment|STR-B MACD Divergence]] (live)
- [[STR-20260728-adaptive-trend|STR-I AdaptiveTrend]] (live)

Detection: ADX(14) > 25 on SPY/BTC benchmark.

## Related
- [[REGIME-ranging]]
- [[REGIME-transitional]]
- [[STRATEGIES-MOC]]
