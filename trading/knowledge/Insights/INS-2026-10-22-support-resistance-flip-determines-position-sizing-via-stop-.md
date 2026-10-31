---
type: insight
date: 2026-10-22
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk_guidelines]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "C065-previous-support-as-future-resistance-in-downtrend", "C064-previous-peaks-as-future-support-in-uptrend"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# Support-resistance flip determines position sizing via stop distance

## Discovery Summary

Concepts C065 and C064 describe how violated support becomes resistance in a downtrend, and how previous peaks become support in an uptrend (Murphy, p. 83). These flip levels directly set logical stop-loss distances: in a downtrend, stops on short entries can be placed just above the former support (now resistance), while in an uptrend, stops on long entries can be placed just below the former peak (now support). The stop distance then determines position size via standard risk-per-trade rules.

## Trading Implication

When a support/resistance flip is identified, compute stop distance from that level and size positions accordingly to keep risk per trade consistent; this aligns technical structure with risk management.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[C064-previous-peaks-as-future-support-in-uptrend]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
