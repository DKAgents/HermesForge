---
type: insight
date: 2026-10-11
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk_guidelines, trading_rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R Role Reversal for Stop Placement & Sizing

## Discovery Summary

The concepts of previous support becoming resistance (C065) and previous peaks becoming support (C064) from Murphy's technical analysis directly inform stop-loss placement. In a downtrend, a short position's stop can be set just above the new resistance level; in an uptrend, a long position's stop can be set just below the new support level. This fixed stop distance then determines position size using a risk-per-trade rule, linking the pattern concept to risk management.

## Trading Implication

When entering a trade based on a trend continuation, identify the nearest violated support (downtrend) or violated resistance (uptrend) and set your stop just beyond that level. Then calculate position size so that the stop-loss distance equals your maximum acceptable loss per trade.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C336-support-level|Support Level]]
- [[C334-resistance-level|Resistance Level]]
