---
type: insight
date: 2026-10-21
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, position sizing, risk guidelines, trading rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Role-reversed S/R levels set stop distance and size

## Discovery Summary

C065's 'previous support as future resistance in downtrend' (Murphy p.83) and C064's mirror rule for previous peaks as future support in uptrend define objective invalidation points on both sides of a trend. The distance from an entry to these flipped support/resistance levels sets the initial stop distance, and with a fixed per-trade risk, position size is derived from that stop distance. This connects Murphy's role-reversal principles directly to the risk guideline that stop placement determines position size.

## Trading Implication

In an uptrend, buy pullbacks near former peaks and place stops below them; in a downtrend, sell rallies into former support and place stops above it. Size each position so the dollar risk from entry to the flipped S/R level equals your predetermined account risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[C334-resistance-level|Resistance Level]]
- [[INS-2026-09-05-support-resistance-levels-set-stops-and-position-size|Support/Resistance Levels Set Stops and Position Size]]
