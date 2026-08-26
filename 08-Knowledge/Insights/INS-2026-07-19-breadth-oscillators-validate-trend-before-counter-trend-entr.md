---
type: insight
date: 2026-07-19
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
# Breadth Oscillators Validate Trend Before Counter-Trend Entry

## Discovery Summary

EN041 prescribes buying oversold conditions in uptrends and selling overbought in downtrends, but oscillators frequently generate false counter-trend signals during strong trending moves — the classic 'oscillators lie in strong trends' problem. C366 defines secondary trends as counter-primary corrections lasting weeks to months, precisely the context where an oscillator reading oversold may reflect a secondary trend correction rather than a true reversal. N186's McClellan Oscillator, being a breadth-based measure, provides a market-wide structural filter: if the McClellan Oscillator confirms broad market weakness during an individual stock's 'oversold' reading, the signal is more likely to reflect a genuine secondary correction rather than an extreme to fade, helping distinguish actionable oversold entries from false floors in strong downtrends.

## Trading Implication

Before executing an oscillator-based oversold buy in an uptrend (EN041), require the McClellan Oscillator to also be in oversold territory or crossing upward, confirming broad market breadth supports a secondary trend correction low rather than a continuing primary downtrend.

## Supporting Notes

- [[C366-secondary-trends]]
- [[EN041-oscillator-entry-strategy-in-trending-markets]]
- [[N186-mcclellan-oscillator]]

## Connection Type

**adds_condition** — Actionability score: 4/5

## Related
- [[RG017-overboughtoversold-readings-in-strong-trends]] — See RG017-overboughtoversold-readings-in-strong-trends for why oscillators fail in strong trends

- [[R127-zero-line-crossings-must-align-with-prevailing-trend]] — See R127-zero-line-crossings-must-align-with-prevailing-trend for the trend-alignment rule that prevents false counter-trend signals.

- [[R268-technical-analysis-checklist-market-analysis-phase]] — See breadth oscillator validation for counter-trend entries

- [[EN086-counter-trend-oscillator-based-trading]] — Refines the basic counter-trend oscillator rule with breadth validation
