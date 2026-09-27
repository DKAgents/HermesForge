---
type: regime
regime_type: low-volatility
description: "Suppressed volatility with small daily ranges, VIX < 15 or ATR < 0.5x average"
indicators: [VIX < 15, ATR < 0.5x 50-day average, Bollinger Bands narrow]
applicable_strategies: [STR-J]
tags: [regime, low-volatility]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# Regime: Low Volatility

Suppressed market volatility with small daily price ranges. Mean-reversion strategies tend to perform well as prices stay within narrow bands.

## Strategies That Work Here

- [[STR-20260726-eufearia-cci-reversal|STR-J EUFEARIA CCI]] — mean-reversion with tight ATR stops benefits from low volatility

## Key Indicators

- VIX < 15
- ATR < 0.5x its 50-day average
- Bollinger Bands narrow (squeeze)
- Small true range bars

## Related
- [[REGIME-high-volatility]]
- [[STRATEGIES-MOC]]

## Active Strategy Mapping (Regime-Aware Pipeline)

Strategies activated when this regime is detected:
- [[STR-20260726-eufearia-cci-reversal|STR-J EUFEARIA CCI]] (watch)
- [[STR-20260730-atr-contraction-breakout|STR-L ATR Contraction]] (watch)

Detection: ATR(14)/Close < 0.5x its 50-day average on SPY/BTC benchmark.
