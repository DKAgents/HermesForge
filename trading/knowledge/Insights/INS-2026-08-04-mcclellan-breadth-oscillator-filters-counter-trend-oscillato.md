---
type: insight
date: 2026-08-04
actionability: 4
connection_type: adds_condition
domains: [concepts, indicators, rules]
sources: ["C366-secondary-trends", "EN041-oscillator-entry-strategy-in-trending-markets", "N186-mcclellan-oscillator"]
seed_id: oscillator_trending_market
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# McClellan Breadth Oscillator Filters Counter-Trend Oscillator Lies

## Discovery Summary

EN041 warns traders to use oscillators with the primary trend (buy oversold in uptrend, sell overbought in downtrend), implicitly acknowledging the known problem of oscillators staying overbought/oversold in strong trends. C366 defines secondary trends as counter-primary corrections lasting weeks to months — precisely the window where traders are most tempted to fade the trend using oscillators. N186's McClellan Oscillator adds a non-obvious solution: because it measures broad market breadth rather than price momentum of a single instrument, it can distinguish genuine secondary-trend corrections (broad deterioration in advancing issues) from mere oscillator 'lies' caused by momentum persistence in a strong trend. A secondary trend confirmed by deteriorating McClellan breadth is more tradeable than an overbought price oscillator alone.

## Trading Implication

Before acting on an overbought/oversold oscillator signal against the primary trend, require McClellan Oscillator confirmation that breadth is genuinely reversing; without that breadth confirmation, treat the oscillator signal as a likely 'lie' in a strong trend and stand aside.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related Notes
- [[INS-2026-08-22-use-breadth-oscillator-to-filter-counter-trend-oscillator-si|Use Breadth Oscillator to Filter Counter-Trend Oscillator Signals]]
