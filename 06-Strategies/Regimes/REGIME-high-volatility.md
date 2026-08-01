---
type: regime
regime_type: high-volatility
description: "Elevated volatility with large daily ranges, VIX > 25 or ATR > 2x average"
indicators: [VIX > 25, ATR > 2x 50-day average, wide Bollinger Bands]
applicable_strategies: []
tags: [regime, high-volatility]
---

# Regime: High Volatility

Elevated market volatility with large daily price ranges. Risk management becomes paramount — position sizing must account for wider stops.

## Strategies That Work Here

No strategies currently target this regime. High volatility increases option-like payoffs for breakout strategies but also increases false signal rates.

## Key Indicators

- VIX > 25
- ATR > 2x its 50-day average
- Bollinger Bands abnormally wide
- Large true range bars

## Research Opportunity

High-volatility regimes may benefit from volatility-breakout strategies (STR-C was killed but the idea may work with better filtering). Also a candidate for reduced position sizing across all live strategies.

## Related
- [[REGIME-low-volatility]]
- [[RISK_RULES]]
- [[STRATEGIES-MOC]]
