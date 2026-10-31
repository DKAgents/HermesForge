---
type: insight
date: 2026-10-17
actionability: 5
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
# S/R flips determine stop distance for position sizing

## Discovery Summary

C065 (Previous Support as Future Resistance in Downtrend, Murphy p.83) and C064 (Previous Peaks as Future Support in Uptrend) identify key reversal levels. The seed question connects these levels to stop distance, which directly determines position size via risk management. Thus, prior support/resistance flips provide objective stop placements for consistent position sizing.

## Trading Implication

In a downtrend, set short stop-loss just above previous support (now resistance); in an uptrend, set long stop just below previous resistance (now support). Then size the position so that the dollar risk (stop distance × position size) equals the trader's fixed risk per trade.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 5/5
