---
type: insight
date: 2026-11-16
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, position_sizing, risk_management, support_resistance, trading_rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
topic: general
confidence: high
has_quotes: false
source: unknown
---
# S/R levels define stops and position size

## Discovery Summary

C065 Previous Support as Future Resistance in Downtrend and EN069 Price Gaps as Support and Resistance for Timing both identify objective S/R zones where entries and protective stops should be placed. In EN069, stop goes beyond the gap; in C065, old support becomes resistance, giving a short-entry zone with a stop above it. The distance from entry to that S/R stop is per-unit risk, which with a fixed account risk determines position size. This connects Murphy's S/R concepts directly to risk and position sizing rules.

## Trading Implication

When price reaches a defined S/R zone from these rules, enter in the direction of the trend and place the stop just beyond the zone; size the position so that stop distance multiplied by position size equals your predetermined account risk.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5
