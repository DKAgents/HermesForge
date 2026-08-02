---
type: regime
regime_type: transitional
description: "Market transitioning between trend and range, high uncertainty"
indicators: [ADX falling from >25 to <20, volatility expanding, Bollinger Bands widening]
applicable_strategies: []
tags: [regime, transitional]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Regime: Transitional

Market is transitioning between trending and ranging states. This is the hardest regime for systematic strategies — trend signals are failing but mean-reversion hasn't yet become reliable.

## Strategies That Work Here

No strategies currently target this regime directly. This is a known gap in the HermesForge strategy portfolio.

## Strategies That Fail Here

- Trend-following strategies (STR-I) get whipsawed
- Mean-reversion strategies (STR-J) enter too early before the range establishes

## Key Indicators

- ADX falling from >25 toward <20
- Volatility expanding
- Bollinger Bands widening after squeeze
- Price crossing 200-day SMA frequently

## Research Opportunity

This regime is under-explored. A strategy that detects regime transition early (e.g., ADX rate-of-change + Bollinger Band expansion) could fill this gap.

## Related
- [[REGIME-trending]]
- [[REGIME-ranging]]
- [[STRATEGIES-MOC]]

## Active Strategy Mapping (Regime-Aware Pipeline)

No strategies currently mapped to transitional regime (STR-K killed).
Near-miss scanner (STR-D) runs regardless of regime.

Detection: ADX falling from >25 toward <20, ATR ratio > 1.2x, BB width expanding.
